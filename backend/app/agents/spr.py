import asyncio
import json
import logging
import math
from datetime import datetime, timezone
from typing import List, Dict, Any

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from backend.app.config import settings

# Configure module logger
logger = logging.getLogger(__name__)


# ============================================================================
# 1. Pydantic Models
# ============================================================================

class SPRStatusInput(BaseModel):
    scenario_id: str = Field(
        ...,
        description="Unique scenario identifier e.g. SIM-HORMUZ-001"
    )
    daily_supply_deficit_mbpd: float = Field(
        ...,
        ge=0.0,
        description="Unmet daily crude demand in million barrels/day"
    )
    estimated_crisis_duration_days: int = Field(
        ...,
        ge=1,
        description="Projected supply outage duration in days"
    )
    total_spr_capacity_mb: float = Field(
        default=39.5,
        gt=0.0,
        description="Total national SPR capacity across Visakhapatnam, Mangalore, and Padur in million barrels"
    )
    current_spr_stock_mb: float = Field(
        default=30.0,
        ge=0.0,
        description="Current inventory in million barrels"
    )
    max_daily_discharge_rate_mbpd: float = Field(
        default=1.2,
        gt=0.0,
        description="Maximum physical discharge throughput rate in million barrels/day"
    )
    strategic_floor_pct: float = Field(
        default=25.0,
        ge=0.0,
        le=100.0,
        description="Mandatory minimum buffer percentage reserved for national security/defense"
    )


class DrawdownDaySchedule(BaseModel):
    day: int = Field(..., description="Day number of crisis drawdown schedule")
    drawdown_volume_mbpd: float = Field(..., description="Volume released from SPR on this day in million barrels/day")
    remaining_stock_mb: float = Field(..., description="Stock remaining at end of day in million barrels")
    stock_capacity_pct: float = Field(..., description="Percentage of total SPR capacity remaining at end of day")
    days_of_runway_left: float = Field(..., description="Remaining supply cover days at current daily deficit")


class SPROptimizationResult(BaseModel):
    daily_schedule: List[DrawdownDaySchedule] = Field(..., description="Daily release trajectory over crisis duration")
    total_drawn_mb: float = Field(..., description="Total cumulative volume drawn from SPR in million barrels")
    final_remaining_stock_mb: float = Field(..., description="Final remaining SPR inventory in million barrels")
    average_daily_release_mbpd: float = Field(..., description="Average daily release rate over crisis duration in million barrels/day")
    floor_breached: bool = Field(..., description="True if final remaining stock fell below strategic floor buffer")
    recommended_replenishment_start_day: int = Field(..., description="Recommended day index to begin reserve replenishment")
    alert_level: str = Field(..., description="National SPR security alert level: GREEN, AMBER, RED, or CRITICAL_DEFENSE_RESERVE_ONLY")


class SPRPolicyNarrative(BaseModel):
    policy_briefing: str = Field(
        ...,
        description="2-3 concise sentences for Ministry of Petroleum & Natural Gas decision makers summarizing operational status and drawdown directive"
    )
    inter_agency_actions: List[str] = Field(
        ...,
        description="Action items for MoPNG, ISPRL, Ministry of Defense, and Oil Refining Companies"
    )
    replenishment_strategy: str = Field(
        ...,
        description="Post-crisis recovery plan including target crude market price thresholds"
    )


class SPRPolicyReport(BaseModel):
    scenario_id: str = Field(..., description="Scenario identifier")
    optimization: SPROptimizationResult = Field(..., description="Detailed quantitative drawdown schedule and metrics")
    policy_briefing: str = Field(..., description="Executive policy briefing for MoPNG leadership")
    inter_agency_actions: List[str] = Field(..., description="Coordinated action directives for key agencies and refiners")
    replenishment_strategy: str = Field(..., description="Strategic post-crisis stock recovery plan")
    timestamp: str = Field(..., description="ISO timestamp of report generation")


# ============================================================================
# 2. Strategic Reserve Drawdown Calculation Engine
# ============================================================================

def calculate_spr_drawdown_schedule(params: SPRStatusInput) -> SPROptimizationResult:
    """
    Calculates a multi-phase daily Strategic Petroleum Reserve (SPR) release trajectory over
    the crisis duration using deterministic curve math.
    """
    strategic_floor_mb = params.total_spr_capacity_mb * (params.strategic_floor_pct / 100.0)
    current_stock = params.current_spr_stock_mb
    
    # Phase 1 applies to the first 30% of crisis days
    phase1_cutoff_day = max(1, math.ceil(params.estimated_crisis_duration_days * 0.30))
    
    daily_schedule: List[DrawdownDaySchedule] = []

    for day in range(1, params.estimated_crisis_duration_days + 1):
        if day <= phase1_cutoff_day:
            # Phase 1 (Initial Shock): Full protection up to maximum discharge throughput
            desired_release = min(params.daily_supply_deficit_mbpd, params.max_daily_discharge_rate_mbpd)
        else:
            # Phase 2 (Tapered Protection): Extend runway if stock approaches strategic floor
            if current_stock <= strategic_floor_mb * 1.1:
                desired_release = min(params.daily_supply_deficit_mbpd, 0.5 * params.max_daily_discharge_rate_mbpd)
            else:
                desired_release = min(params.daily_supply_deficit_mbpd, params.max_daily_discharge_rate_mbpd)

        # Enforce hard zero cap - never allow stock to deplete below 0.0
        actual_release = min(desired_release, current_stock)
        actual_release = max(0.0, actual_release)

        current_stock -= actual_release
        stock_capacity_pct = (current_stock / params.total_spr_capacity_mb) * 100.0

        if params.daily_supply_deficit_mbpd > 0:
            runway_days = current_stock / params.daily_supply_deficit_mbpd
        else:
            runway_days = 999.0

        daily_schedule.append(
            DrawdownDaySchedule(
                day=day,
                drawdown_volume_mbpd=round(actual_release, 4),
                remaining_stock_mb=round(current_stock, 4),
                stock_capacity_pct=round(stock_capacity_pct, 2),
                days_of_runway_left=round(runway_days, 2)
            )
        )

    total_drawn = sum(sched.drawdown_volume_mbpd for sched in daily_schedule)
    final_stock = current_stock
    avg_daily_release = total_drawn / params.estimated_crisis_duration_days if params.estimated_crisis_duration_days > 0 else 0.0
    floor_breached = final_stock < strategic_floor_mb
    recommended_replenishment_day = params.estimated_crisis_duration_days + 1

    # Determine alert level based on final stock capacity percentage
    final_capacity_pct = (final_stock / params.total_spr_capacity_mb) * 100.0
    if final_capacity_pct > 60.0:
        alert_level = "GREEN"
    elif final_capacity_pct > 35.0:
        alert_level = "AMBER"
    elif final_capacity_pct > 25.0:
        alert_level = "RED"
    else:
        alert_level = "CRITICAL_DEFENSE_RESERVE_ONLY"

    return SPROptimizationResult(
        daily_schedule=daily_schedule,
        total_drawn_mb=round(total_drawn, 4),
        final_remaining_stock_mb=round(final_stock, 4),
        average_daily_release_mbpd=round(avg_daily_release, 4),
        floor_breached=floor_breached,
        recommended_replenishment_start_day=recommended_replenishment_day,
        alert_level=alert_level
    )


# ============================================================================
# 3. Gemini 2.5 Flash Policy Engine with Self-Looping
# ============================================================================

def generate_spr_policy_narrative(params: SPRStatusInput, opt: SPROptimizationResult) -> Dict[str, Any]:
    """
    Invokes Gemini 2.5 Flash to synthesize executive policy directives, inter-agency actions,
    and post-crisis replenishment plans. Implements a self-healing retry loop (up to 3 attempts)
    with error feedback incorporated on schema/JSON validation failures.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    max_retries = 3
    attempt = 0
    error_feedback = ""

    system_instruction = (
        "You are the Director of Strategic Energy Reserves for Project Argos (AI-Driven Energy "
        "Supply Chain Resilience Platform for India). Provide authoritative, realistic policy briefings, "
        "inter-agency escalation directives, and crude replenishment strategies for the Ministry of Petroleum "
        "& Natural Gas (MoPNG) and Indian Strategic Petroleum Reserves Limited (ISPRL)."
    )

    base_prompt = f"""
    Analyze the following Strategic Petroleum Reserve (SPR) drawdown optimization results and generate a policy report.

    Input Status & Scenario:
    - Scenario ID: {params.scenario_id}
    - Daily Supply Deficit: {params.daily_supply_deficit_mbpd} mbpd
    - Crisis Duration: {params.estimated_crisis_duration_days} days
    - Total Reserve Capacity: {params.total_spr_capacity_mb} mb (Visakhapatnam, Mangalore, Padur)
    - Initial SPR Stock: {params.current_spr_stock_mb} mb
    - Maximum Discharge Rate: {params.max_daily_discharge_rate_mbpd} mbpd
    - Strategic Floor Buffer: {params.strategic_floor_pct}% ({params.total_spr_capacity_mb * params.strategic_floor_pct / 100.0:.2f} mb)

    Drawdown Optimization Metrics:
    - Total Volume Drawn: {opt.total_drawn_mb} mb
    - Final Remaining Stock: {opt.final_remaining_stock_mb} mb ({opt.final_remaining_stock_mb / params.total_spr_capacity_mb * 100.0:.1f}% capacity)
    - Average Daily Release Rate: {opt.average_daily_release_mbpd} mbpd
    - Strategic Floor Breached: {opt.floor_breached}
    - Alert Level: {opt.alert_level}
    - Recommended Replenishment Start Day: Day {opt.recommended_replenishment_start_day}

    Required Output JSON Schema:
    - policy_briefing: A 2-3 sentence executive summary for MoPNG leadership detailing operational posture and strategic drawdown necessity.
    - inter_agency_actions: Array of 4-6 specific actionable directives for MoPNG, ISPRL, Ministry of Defense, and Indian Refiners (IOCL, BPCL, HPCL, Reliance).
    - replenishment_strategy: Strategic post-crisis recovery plan specifying timing, target price thresholds (e.g., Dated Brent < $75/bbl), and supplier diversification.
    """

    while attempt < max_retries:
        attempt += 1
        prompt = base_prompt
        if error_feedback:
            prompt += f"\n\nCRITICAL FIX REQUIRED FROM PREVIOUS ATTEMPT:\nYour previous response failed validation with error: {error_feedback}. Ensure strict compliance with the expected JSON structure."

        try:
            logger.info(f"Invoking Gemini 2.5 Flash SPR policy engine (Attempt {attempt}/{max_retries})...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=SPRPolicyNarrative,
                    temperature=0.2,
                )
            )

            if not response.text:
                raise ValueError("Received empty response payload from Gemini API.")

            narrative = SPRPolicyNarrative.model_validate_json(response.text)
            logger.info("Successfully generated and validated SPR policy narrative from Gemini.")
            return narrative.model_dump()

        except Exception as e:
            error_feedback = str(e)
            logger.warning(f"Attempt {attempt}/{max_retries} SPR policy narrative error: {error_feedback}")
            if attempt >= max_retries:
                logger.error("All retries exhausted for Gemini SPR policy narrative generation.")
                raise RuntimeError(
                    f"Gemini SPR policy narrative generation failed after {max_retries} attempts: {error_feedback}"
                ) from e

    raise RuntimeError("Unexpected failure in retry loop execution.")


# ============================================================================
# 4. Main Agent Orchestrator Function
# ============================================================================

async def run_spr_optimiser(params: SPRStatusInput) -> SPRPolicyReport:
    """
    Main Orchestrator Function for the Strategic Petroleum Reserve (SPR) Optimiser Agent.
    1. Computes deterministic multi-phase drawdown schedule and capacity metrics.
    2. Invokes Gemini 2.5 Flash policy engine (with self-healing retry loop) for executive directives.
    3. Combines quantitative and narrative outputs into a complete SPRPolicyReport.
    4. Includes graceful fallback logic to guarantee non-blocking execution and zero 500 API errors.
    """
    logger.info(f"Executing SPR Optimization Agent for scenario '{params.scenario_id}'.")

    # Step 1: Execute quantitative drawdown curve calculation
    opt_result = calculate_spr_drawdown_schedule(params)

    # Step 2: Generate LLM policy directives with fallback safety net
    try:
        narrative = await asyncio.to_thread(generate_spr_policy_narrative, params, opt_result)
    except Exception as e:
        logger.error(f"Fallback triggered for SPR agent under scenario '{params.scenario_id}' due to error: {str(e)}")
        
        final_pct = (opt_result.final_remaining_stock_mb / params.total_spr_capacity_mb) * 100.0
        narrative = {
            "policy_briefing": (
                f"Under scenario {params.scenario_id}, an estimated daily crude deficit of {params.daily_supply_deficit_mbpd:.2f} mbpd "
                f"over {params.estimated_crisis_duration_days} days necessitates a cumulative SPR release of {opt_result.total_drawn_mb:.2f} million barrels. "
                f"Ending SPR inventory stands at {opt_result.final_remaining_stock_mb:.2f} mb ({final_pct:.1f}% capacity) "
                f"with national security alert level classified as {opt_result.alert_level}."
            ),
            "inter_agency_actions": [
                "MoPNG: Issue emergency executive decree authorizing ISPRL to initiate phased crude discharge from strategic caverns.",
                "ISPRL: Activate main cavern discharge pumps at Visakhapatnam, Mangalore, and Padur to deliver crude to coastal refinery terminals.",
                "Ministry of Defense: Secure mandatory strategic crude floor buffer to ensure uninterrupted operational fuel supply for defense forces.",
                "Indian Refiners (IOCL, BPCL, HPCL): Re-calibrate refinery distillation units to handle SPR crude slates and prioritize high-demand diesel production.",
                "Ministry of External Affairs: Engage international energy forums (IEA / OPEC+) to coordinate global inventory releases and stabilize crude benchmarks."
            ],
            "replenishment_strategy": (
                f"Schedule post-crisis reserve replenishment to begin on Day {opt_result.recommended_replenishment_start_day} (post-stabilization). "
                "Execute phased spot purchases when Dated Brent crude drops below $75/bbl and secure long-term bilateral supply contracts with non-disrupted producers."
            )
        }

    timestamp = datetime.now(timezone.utc).isoformat()

    report = SPRPolicyReport(
        scenario_id=params.scenario_id,
        optimization=opt_result,
        policy_briefing=narrative["policy_briefing"],
        inter_agency_actions=narrative["inter_agency_actions"],
        replenishment_strategy=narrative["replenishment_strategy"],
        timestamp=timestamp
    )

    logger.info(f"SPR Optimization Agent execution for scenario '{params.scenario_id}' completed successfully.")
    return report
