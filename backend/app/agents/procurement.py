import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import numpy as np
from scipy.optimize import linprog
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from backend.app.config import settings

# Configure module logger
logger = logging.getLogger(__name__)


# ============================================================================
# 1. Pydantic Models
# ============================================================================

class CrudeOption(BaseModel):
    crude_name: str = Field(
        ...,
        description="Name of crude grade e.g. Basrah Medium, West African Forcados, Brazilian Tupi"
    )
    origin_country: str = Field(
        ...,
        description="Country of origin"
    )
    api_gravity: float = Field(
        ...,
        description="API gravity degree e.g. 30.5"
    )
    sulfur_pct: float = Field(
        ...,
        description="Percentage sulfur content w/w e.g. 1.2"
    )
    spot_price_usd_bbl: float = Field(
        ...,
        description="FOB spot price in USD per barrel"
    )
    freight_risk_premium_usd_bbl: float = Field(
        ...,
        description="Freight and risk premium in USD per barrel"
    )
    max_availability_mbpd: float = Field(
        ...,
        description="Maximum available spot volume in million barrels/day"
    )
    lead_time_days: int = Field(
        ...,
        description="Transit and delivery lead time in days"
    )


class RefineryRequirement(BaseModel):
    refinery_name: str = Field(
        ...,
        description="Target refinery name e.g. Jamnagar Refinery, IOCL Paradip"
    )
    target_deficit_mbpd: float = Field(
        ...,
        gt=0.0,
        description="Crude supply volume shortfall to fulfill in million barrels/day"
    )
    min_api_gravity: float = Field(
        ...,
        description="Minimum acceptable blended API gravity degree"
    )
    max_sulfur_pct: float = Field(
        ...,
        description="Maximum acceptable blended sulfur percentage"
    )


class ProcurementAllocation(BaseModel):
    crude_name: str = Field(..., description="Selected crude grade name")
    origin_country: str = Field(..., description="Country of origin")
    allocated_mbpd: float = Field(..., description="Allocated crude volume in million barrels/day")
    total_landed_cost_usd_bbl: float = Field(..., description="Total landed cost per barrel (spot price + freight premium)")
    lead_time_days: int = Field(..., description="Delivery lead time in days")


class OptimizationResult(BaseModel):
    allocations: List[ProcurementAllocation] = Field(..., description="List of crude allocations satisfying requirements")
    total_procured_mbpd: float = Field(..., description="Total crude volume procured in million barrels/day")
    unfilled_deficit_mbpd: float = Field(..., description="Remaining unfilled deficit in million barrels/day")
    total_daily_cost_usd: float = Field(..., description="Total daily landed cost in USD")
    weighted_api_gravity: float = Field(..., description="Volume-weighted average API gravity degree")
    weighted_sulfur_pct: float = Field(..., description="Volume-weighted average sulfur percentage")
    optimization_status: str = Field(..., description="Optimization status: OPTIMAL, FEASIBLE_WITH_SLACK, or INFEASIBLE")


class ProcurementNarrative(BaseModel):
    executive_summary: str = Field(..., description="2-3 sentences detailing optimal purchasing strategy")
    actionable_steps: List[str] = Field(..., description="Step-by-step instructions for procurement desks")
    risk_tradeoffs: List[str] = Field(..., description="Cost vs quality vs lead-time compromises")


class ProcurementRecommendationReport(BaseModel):
    scenario_id: str = Field(..., description="Scenario simulation ID")
    refinery_name: str = Field(..., description="Refinery name")
    optimization: OptimizationResult = Field(..., description="Mathematical optimization result")
    executive_summary: str = Field(..., description="Executive summary detailing optimal purchasing strategy")
    actionable_steps: List[str] = Field(..., description="Step-by-step instructions for procurement desks")
    risk_tradeoffs: List[str] = Field(..., description="Cost vs quality vs lead-time compromises")
    timestamp: str = Field(..., description="ISO timestamp of recommendation generation")


# ============================================================================
# 2. Scipy Linear Optimization Engine
# ============================================================================

def solve_procurement_optimization(
    req: RefineryRequirement,
    candidates: Optional[List[CrudeOption]] = None
) -> OptimizationResult:
    """
    Mathematical matching of crude spot markets to refinery quality constraints using scipy.optimize.linprog.
    Implements automatic slack relaxation fallback if strict constraints prove infeasible.
    """
    if not candidates:
        candidates = [
            CrudeOption(
                crude_name="Basrah Medium",
                origin_country="Iraq",
                api_gravity=29.0,
                sulfur_pct=2.50,
                spot_price_usd_bbl=76.50,
                freight_risk_premium_usd_bbl=3.20,
                max_availability_mbpd=1.0,
                lead_time_days=12
            ),
            CrudeOption(
                crude_name="West African Forcados",
                origin_country="Nigeria",
                api_gravity=34.5,
                sulfur_pct=0.20,
                spot_price_usd_bbl=82.00,
                freight_risk_premium_usd_bbl=4.50,
                max_availability_mbpd=0.6,
                lead_time_days=18
            ),
            CrudeOption(
                crude_name="Brazilian Tupi",
                origin_country="Brazil",
                api_gravity=30.2,
                sulfur_pct=0.40,
                spot_price_usd_bbl=80.00,
                freight_risk_premium_usd_bbl=5.80,
                max_availability_mbpd=0.8,
                lead_time_days=25
            ),
            CrudeOption(
                crude_name="UAE Murban",
                origin_country="UAE",
                api_gravity=40.2,
                sulfur_pct=0.78,
                spot_price_usd_bbl=83.50,
                freight_risk_premium_usd_bbl=2.80,
                max_availability_mbpd=0.7,
                lead_time_days=10
            ),
            CrudeOption(
                crude_name="US WTI Midland",
                origin_country="USA",
                api_gravity=40.0,
                sulfur_pct=0.20,
                spot_price_usd_bbl=79.50,
                freight_risk_premium_usd_bbl=6.20,
                max_availability_mbpd=0.5,
                lead_time_days=28
            )
        ]

    n = len(candidates)
    landed_costs = np.array([c.spot_price_usd_bbl + c.freight_risk_premium_usd_bbl for c in candidates])

    # Objective: Minimize total landed cost + penalty on unfulfilled deficit
    # Penalty per mbpd unfilled (USD 10,000 / barrel) to maximize volume fulfillment up to deficit
    penalty_M = 10000.0
    c_obj = landed_costs - penalty_M

    bounds = [(0.0, float(c.max_availability_mbpd)) for c in candidates]

    def build_constraint_matrices(min_api: float, max_sulfur: float):
        # A_ub @ x <= b_ub
        # Row 0: Volume constraint: sum(x_i) <= req.target_deficit_mbpd
        # Row 1: Min API Gravity linearized: sum(x_i * (min_api - api_i)) <= 0
        # Row 2: Max Sulfur Content linearized: sum(x_i * (sulfur_i - max_sulfur)) <= 0
        A_ub = np.zeros((3, n))
        b_ub = np.zeros(3)

        A_ub[0, :] = 1.0
        b_ub[0] = req.target_deficit_mbpd

        for i, cand in enumerate(candidates):
            A_ub[1, i] = min_api - cand.api_gravity
            A_ub[2, i] = cand.sulfur_pct - max_sulfur

        return A_ub, b_ub

    # Attempt 1: Solve strict model
    A_ub, b_ub = build_constraint_matrices(req.min_api_gravity, req.max_sulfur_pct)
    res = linprog(c=c_obj, A_ub=A_ub, b_ub=b_ub, bounds=bounds, method="highs")

    opt_status = "OPTIMAL"

    # Attempt 2: Slack solver relaxation fallback if strict bounds are infeasible
    if not res.success or res.x is None:
        logger.warning("Strict linear programming optimization infeasible. Invoking relaxed slack solver...")
        A_ub_relaxed, b_ub_relaxed = build_constraint_matrices(
            min_api=req.min_api_gravity - 1.5,
            max_sulfur=req.max_sulfur_pct + 0.3
        )
        res = linprog(c=c_obj, A_ub=A_ub_relaxed, b_ub=b_ub_relaxed, bounds=bounds, method="highs")

        if res.success and res.x is not None:
            opt_status = "FEASIBLE_WITH_SLACK"
        else:
            logger.error("Relaxed linear programming solver failed. Generating greedy cost allocation.")
            opt_status = "INFEASIBLE"

    if opt_status in ("OPTIMAL", "FEASIBLE_WITH_SLACK"):
        x_allocated = np.maximum(0.0, res.x)
    else:
        # Greedy fallback: Sort candidates by landed cost, allocate up to availability
        sorted_indices = np.argsort(landed_costs)
        x_allocated = np.zeros(n)
        rem_deficit = req.target_deficit_mbpd
        for idx in sorted_indices:
            avail = candidates[idx].max_availability_mbpd
            take = min(rem_deficit, avail)
            x_allocated[idx] = take
            rem_deficit -= take

    # Process allocations and aggregate metrics
    total_procured = float(np.sum(x_allocated))
    unfilled_deficit = max(0.0, float(req.target_deficit_mbpd - total_procured))

    allocations: List[ProcurementAllocation] = []
    total_daily_cost = 0.0
    weighted_api_sum = 0.0
    weighted_sulfur_sum = 0.0

    for i, cand in enumerate(candidates):
        vol = float(x_allocated[i])
        if vol > 1e-4:
            landed_cost = float(cand.spot_price_usd_bbl + cand.freight_risk_premium_usd_bbl)
            allocations.append(
                ProcurementAllocation(
                    crude_name=cand.crude_name,
                    origin_country=cand.origin_country,
                    allocated_mbpd=round(vol, 4),
                    total_landed_cost_usd_bbl=round(landed_cost, 2),
                    lead_time_days=cand.lead_time_days
                )
            )
            total_daily_cost += vol * 1_000_000.0 * landed_cost
            weighted_api_sum += vol * cand.api_gravity
            weighted_sulfur_sum += vol * cand.sulfur_pct

    weighted_api = (weighted_api_sum / total_procured) if total_procured > 0 else 0.0
    weighted_sulfur = (weighted_sulfur_sum / total_procured) if total_procured > 0 else 0.0

    return OptimizationResult(
        allocations=allocations,
        total_procured_mbpd=round(total_procured, 4),
        unfilled_deficit_mbpd=round(unfilled_deficit, 4),
        total_daily_cost_usd=round(total_daily_cost, 2),
        weighted_api_gravity=round(weighted_api, 2),
        weighted_sulfur_pct=round(weighted_sulfur, 2),
        optimization_status=opt_status
    )


# ============================================================================
# 3. Gemini 2.5 Flash Strategy Engine with Self-Looping
# ============================================================================

def generate_procurement_narrative(
    req: RefineryRequirement,
    opt: OptimizationResult
) -> Dict[str, Any]:
    """
    Calls Gemini 2.5 Flash to synthesize procurement recommendations, trade-off analysis,
    and step-by-step buyer directives. Implements a self-healing retry loop (up to 3 attempts)
    with error feedback re-prompting.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    max_retries = 3
    attempt = 0
    error_feedback = ""

    system_instruction = (
        "You are the Senior Crude Oil Procurement & Strategy Executive for Indian public sector "
        "and private refineries (IOCL, BPCL, HPCL, Reliance). Provide authoritative, realistic, "
        "and actionable spot-market crude purchasing directives based on linear optimization results."
    )

    allocations_summary = json.dumps([a.model_dump() for a in opt.allocations], indent=2)

    base_prompt = f"""
    Review the following linear optimization procurement results for {req.refinery_name} and generate strategic buying directives.

    Refinery Target Constraints:
    - Target Refinery Name: {req.refinery_name}
    - Target Deficit to Fulfill: {req.target_deficit_mbpd} mbpd
    - Minimum API Gravity Required: {req.min_api_gravity}
    - Maximum Sulfur Content Allowed: {req.max_sulfur_pct}%

    Optimization Results ({opt.optimization_status}):
    - Total Volume Procured: {opt.total_procured_mbpd} mbpd (Unfilled Deficit: {opt.unfilled_deficit_mbpd} mbpd)
    - Total Daily Spend: ${opt.total_daily_cost_usd:,.2f} USD
    - Blended API Gravity: {opt.weighted_api_gravity} (Target Min: {req.min_api_gravity})
    - Blended Sulfur Content: {opt.weighted_sulfur_pct}% (Target Max: {req.max_sulfur_pct}%)

    Crude Allocations:
    {allocations_summary}

    Required Output JSON Schema:
    - executive_summary: A 2-3 sentence executive briefing detailing the optimal purchasing strategy and financial commitment.
    - actionable_steps: An array of 4-6 specific, step-by-step tactical directives for refinery procurement desks (e.g. chartering VLCCs, hedging spot price risk, opening LCs with state banks).
    - risk_tradeoffs: An array of 4-6 explicit trade-off considerations analyzing cost vs quality (API/Sulfur blend) vs shipping lead times.
    """

    while attempt < max_retries:
        attempt += 1
        prompt = base_prompt
        if error_feedback:
            prompt += f"\n\nCRITICAL FIX REQUIRED FROM PREVIOUS ATTEMPT:\nYour previous output failed validation with error: {error_feedback}. Ensure valid JSON matching the exact schema."

        try:
            logger.info(f"Invoking Gemini 2.5 Flash procurement strategy engine (Attempt {attempt}/{max_retries})...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ProcurementNarrative,
                    temperature=0.3,
                )
            )

            if not response.text:
                raise ValueError("Received empty response string from Gemini API.")

            narrative = ProcurementNarrative.model_validate_json(response.text)
            logger.info("Successfully generated and validated procurement strategy from Gemini.")
            return narrative.model_dump()

        except Exception as e:
            error_feedback = str(e)
            logger.warning(
                f"Attempt {attempt}/{max_retries} procurement strategy generation error: {error_feedback}"
            )
            if attempt >= max_retries:
                logger.error("All retries exhausted for Gemini procurement strategy generation.")
                raise RuntimeError(
                    f"Gemini procurement strategy generation failed after {max_retries} attempts: {error_feedback}"
                ) from e

    raise RuntimeError("Unexpected failure in retry loop execution.")


# ============================================================================
# 4. Main Public Agent Interface
# ============================================================================

async def run_procurement_orchestrator(
    scenario_id: str,
    refinery_req: RefineryRequirement,
    candidate_crudes: Optional[List[CrudeOption]] = None
) -> ProcurementRecommendationReport:
    """
    Main Orchestrator for the Adaptive Procurement Orchestrator Agent.
    1. Executes Scipy linear optimization matching spot crude options to refinery constraints.
    2. Passes optimization metrics to Gemini 2.5 Flash for operational recommendations and trade-off analysis.
    3. Combines metrics and LLM outputs into ProcurementRecommendationReport.
    4. Includes graceful fallback logic to guarantee the API NEVER returns a 500 error.
    """
    logger.info(f"Starting procurement orchestrator for scenario '{scenario_id}', refinery '{refinery_req.refinery_name}'.")

    # Step 1: Execute linear optimization
    opt = solve_procurement_optimization(refinery_req, candidate_crudes)

    # Step 2: Generate LLM strategy & trade-off narrative with fallback safety net
    try:
        # Run synchronous Gemini call in thread pool to maintain non-blocking execution
        narrative = await asyncio.to_thread(generate_procurement_narrative, refinery_req, opt)
    except Exception as e:
        logger.error(f"Fallback triggered for procurement scenario '{scenario_id}' due to LLM error: {str(e)}")
        narrative = {
            "executive_summary": (
                f"Optimal procurement plan for {refinery_req.refinery_name} secures {opt.total_procured_mbpd} mbpd "
                f"out of {refinery_req.target_deficit_mbpd} mbpd target deficit at a total daily cost of ${opt.total_daily_cost_usd:,.2f}. "
                f"Blended quality achieves an API gravity of {opt.weighted_api_gravity} and sulfur content of {opt.weighted_sulfur_pct}%."
            ),
            "actionable_steps": [
                f"Issue immediate spot purchasing orders for allocated crude grades totaling {opt.total_procured_mbpd} mbpd.",
                "Establish Letters of Credit (LCs) via state banking syndicates for international crude vendors.",
                "Fixture Very Large Crude Carrier (VLCC) tonnage for Atlantic basin routes (Brazil, West Africa) to mitigate freight spikes.",
                "Implement crude oil futures hedging on MCX/ICE to fix crack spread margins.",
                f"Notify refinery blend managers to adjust desulfurization units based on blended sulfur content of {opt.weighted_sulfur_pct}%."
            ],
            "risk_tradeoffs": [
                f"Lead-time trade-off: Long-haul Atlantic crudes take up to 25-28 days transit versus 10-12 days for Persian Gulf routes.",
                f"Quality balance: Heavy/sweet grades blended to comply with refinery maximum sulfur limit of {refinery_req.max_sulfur_pct}%.",
                f"Unfilled shortfall: {opt.unfilled_deficit_mbpd} mbpd deficit remains unfulfilled due to market supply limits.",
                "Freight price exposure: Elevated maritime risk premiums increase total landed cost per barrel."
            ]
        }

    timestamp = datetime.now(timezone.utc).isoformat()

    report = ProcurementRecommendationReport(
        scenario_id=scenario_id,
        refinery_name=refinery_req.refinery_name,
        optimization=opt,
        executive_summary=narrative["executive_summary"],
        actionable_steps=narrative["actionable_steps"],
        risk_tradeoffs=narrative["risk_tradeoffs"],
        timestamp=timestamp
    )

    logger.info(f"Procurement recommendation report generated successfully for scenario '{scenario_id}'.")
    return report
