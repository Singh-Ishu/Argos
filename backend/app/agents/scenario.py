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

class ScenarioInput(BaseModel):
    scenario_id: str = Field(
        ...,
        description="Unique identifier for the scenario simulation e.g. SIM-HORMUZ-001"
    )
    corridor_name: str = Field(
        ...,
        description="Name of maritime energy corridor e.g. Strait of Hormuz, Red Sea / Bab-el-Mandeb"
    )
    closure_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage closure of corridor (0.0 to 100.0)"
    )
    duration_days: int = Field(
        ...,
        ge=1,
        description="Duration of disruption in days"
    )
    baseline_india_imports_mbpd: float = Field(
        default=5.0,
        gt=0.0,
        description="Total baseline Indian crude import capacity in million barrels/day"
    )
    corridor_baseline_mbpd: float = Field(
        default=2.2,
        ge=0.0,
        description="Baseline crude flow through this specific corridor in million barrels/day"
    )
    spr_total_capacity_mb: float = Field(
        default=39.5,
        gt=0.0,
        description="Total Strategic Petroleum Reserve capacity in million barrels"
    )
    spr_current_stock_mb: float = Field(
        default=30.0,
        ge=0.0,
        description="Current Strategic Petroleum Reserve stock volume in million barrels"
    )


class QuantitativeImpact(BaseModel):
    daily_deficit_mbpd: float = Field(
        ...,
        description="Daily crude import deficit in million barrels/day"
    )
    total_volume_lost_mb: float = Field(
        ...,
        description="Cumulative volume of crude lost over duration in million barrels"
    )
    refinery_capacity_impact_pct: float = Field(
        ...,
        description="Estimated percentage drop in national refinery utilization"
    )
    spr_depletion_days_used: float = Field(
        ...,
        description="Days worth of Strategic Petroleum Reserve consumed during the shock"
    )
    spr_remaining_days_cover: float = Field(
        ...,
        description="Remaining national Strategic Petroleum Reserve runway in days"
    )
    estimated_brent_surge_pct: float = Field(
        ...,
        description="Projected global Brent crude price increase percentage"
    )
    estimated_domestic_fuel_price_surge_pct: float = Field(
        ...,
        description="Projected domestic fuel price increase percentage"
    )
    macro_gdp_drag_pct: float = Field(
        ...,
        description="Estimated quarterly macroeconomic GDP drag percentage"
    )


class ScenarioNarrative(BaseModel):
    executive_briefing: str = Field(
        ...,
        description="2-3 concise sentences summarizing operational severity and strategic vulnerability"
    )
    cascading_impacts: List[str] = Field(
        ...,
        description="Downstream effects on power, logistics, inflation, and key industries"
    )
    recommended_policy_directives: List[str] = Field(
        ...,
        description="Actionable national policy and refiner operational responses"
    )


class ScenarioReport(BaseModel):
    scenario_id: str = Field(..., description="Scenario identifier")
    corridor_name: str = Field(..., description="Corridor name")
    closure_percentage: float = Field(..., description="Percentage closure of corridor")
    duration_days: int = Field(..., description="Duration in days")
    metrics: QuantitativeImpact = Field(..., description="Calculated physical and financial impact metrics")
    executive_briefing: str = Field(..., description="Executive briefing summarizing operational severity")
    cascading_impacts: List[str] = Field(..., description="Cascading socio-economic and industrial impacts")
    recommended_policy_directives: List[str] = Field(..., description="Actionable policy directives for government and refiners")
    simulation_timestamp: str = Field(..., description="ISO timestamp of simulation execution")


# ============================================================================
# 2. Deterministic Calculation Engine
# ============================================================================

def calculate_scenario_metrics(params: ScenarioInput) -> QuantitativeImpact:
    """
    Pure Python deterministic calculation engine for physical and macroeconomic disruption metrics.
    Uses precise ground-truth energy supply chain models.
    """
    # 1. Daily Deficit (mbpd)
    daily_deficit = params.corridor_baseline_mbpd * (params.closure_percentage / 100.0)

    # 2. Total Volume Lost (million barrels)
    total_lost = daily_deficit * params.duration_days

    # 3. National Refinery Capacity Impact (% drop)
    refinery_drop_pct = (daily_deficit / params.baseline_india_imports_mbpd) * 100.0

    # 4. Strategic Petroleum Reserve (SPR) Drawdown Math
    # Capped at maximum technical SPR withdrawal rate of 1.2 mbpd
    spr_drawdown_rate = min(daily_deficit, 1.2)
    spr_consumed_mb = min(params.spr_current_stock_mb, spr_drawdown_rate * params.duration_days)
    spr_remaining_mb = params.spr_current_stock_mb - spr_consumed_mb

    # Days of SPR consumed during the event shock
    spr_depletion_days_used = (spr_consumed_mb / spr_drawdown_rate) if spr_drawdown_rate > 0 else 0.0

    # Remaining reserve runway cover days after event
    # Net effective import flow = baseline imports - unmitigated deficit + SPR cushion
    net_effective_import_rate = params.baseline_india_imports_mbpd - daily_deficit + spr_drawdown_rate
    spr_remaining_days_cover = spr_remaining_mb / max(net_effective_import_rate, 0.001)

    # 5. Financial & Macroeconomic Metrics
    brent_surge_pct = round(
        (params.closure_percentage * 0.15) * (1.0 + (params.duration_days / 30.0) * 0.5),
        2
    )
    domestic_surge_pct = round(brent_surge_pct * 0.65, 2)
    gdp_drag_pct = round(brent_surge_pct * 0.012, 2)

    return QuantitativeImpact(
        daily_deficit_mbpd=round(daily_deficit, 4),
        total_volume_lost_mb=round(total_lost, 2),
        refinery_capacity_impact_pct=round(refinery_drop_pct, 2),
        spr_depletion_days_used=round(spr_depletion_days_used, 2),
        spr_remaining_days_cover=round(spr_remaining_days_cover, 2),
        estimated_brent_surge_pct=brent_surge_pct,
        estimated_domestic_fuel_price_surge_pct=domestic_surge_pct,
        macro_gdp_drag_pct=gdp_drag_pct
    )


# ============================================================================
# 3. Gemini 2.5 Flash Narrative Engine with Self-Looping
# ============================================================================

def generate_scenario_narrative(params: ScenarioInput, metrics: QuantitativeImpact) -> Dict[str, Any]:
    """
    Calls Gemini 2.5 Flash LLM to synthesize narrative briefing, cascading risks,
    and policy directives. Implements a self-healing retry loop (up to 3 attempts)
    with validation feedback on JSON / Pydantic parsing failures.
    """
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    max_retries = 3
    attempt = 0
    error_feedback = ""

    system_instruction = (
        "You are the Chief Energy Security Analyst for Project Argos (AI-Driven Energy Supply Chain "
        "Resilience Platform for India). Provide authoritative, realistic, and highly actionable analysis "
        "of maritime energy supply chain disruptions."
    )

    base_prompt = f"""
    Analyze the following energy disruption scenario for India and synthesize an operational briefing.

    Scenario Parameters:
    - Scenario ID: {params.scenario_id}
    - Transit Corridor: {params.corridor_name}
    - Corridor Blockage: {params.closure_percentage}%
    - Duration: {params.duration_days} days
    - India Total Import Baseline: {params.baseline_india_imports_mbpd} mbpd
    - Corridor Transit Baseline: {params.corridor_baseline_mbpd} mbpd

    Calculated Supply & Macro Impact Metrics:
    - Daily Supply Deficit: {metrics.daily_deficit_mbpd} mbpd
    - Total Volume Lost: {metrics.total_volume_lost_mb} million barrels
    - Refinery Capacity Drop: {metrics.refinery_capacity_impact_pct}%
    - SPR Drawdown Duration Consumed: {metrics.spr_depletion_days_used} days
    - Post-Event SPR Remaining Cover: {metrics.spr_remaining_days_cover} days
    - Estimated Brent Crude Surge: +{metrics.estimated_brent_surge_pct}%
    - Estimated Domestic Fuel Surge: +{metrics.estimated_domestic_fuel_price_surge_pct}%
    - Macro GDP Drag: -{metrics.macro_gdp_drag_pct}%

    Required Output JSON Schema:
    - executive_briefing: A 2-3 concise sentence summary of operational severity and strategic vulnerability.
    - cascading_impacts: Array of 4-6 specific downstream impacts (power grid fuel shifts, freight logistics, inflation, fertilizer & petrochemical sectors).
    - recommended_policy_directives: Array of 4-6 actionable policy and operational directives for the Ministry of Petroleum & Natural Gas and Indian refiners (IOCL, BPCL, HPCL, Reliance).
    """

    while attempt < max_retries:
        attempt += 1
        prompt = base_prompt
        if error_feedback:
            prompt += f"\n\nCRITICAL FIX REQUIRED FROM PREVIOUS ATTEMPT:\nYour previous output failed validation with error: {error_feedback}. Ensure valid JSON matching the exact schema."

        try:
            logger.info(f"Invoking Gemini 2.5 Flash narrative engine (Attempt {attempt}/{max_retries})...")
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ScenarioNarrative,
                    temperature=0.3,
                )
            )

            if not response.text:
                raise ValueError("Received empty response string from Gemini API.")

            # Validate against Pydantic model
            narrative = ScenarioNarrative.model_validate_json(response.text)
            logger.info("Successfully generated and validated scenario narrative from Gemini.")
            return narrative.model_dump()

        except Exception as e:
            error_feedback = str(e)
            logger.warning(
                f"Attempt {attempt}/{max_retries} narrative generation error: {error_feedback}"
            )
            if attempt >= max_retries:
                logger.error("All retries exhausted for Gemini narrative generation.")
                raise RuntimeError(
                    f"Gemini narrative generation failed after {max_retries} attempts: {error_feedback}"
                ) from e

    raise RuntimeError("Unexpected failure in retry loop execution.")


# ============================================================================
# 4. Main Public Agent Interface
# ============================================================================

async def run_scenario_simulation(params: ScenarioInput) -> ScenarioReport:
    """
    Main Orchestrator for the Disruption Scenario Modeller Agent.
    1. Computes deterministic physical and financial impact metrics.
    2. Synthesizes narrative & cascading impacts via Gemini 2.5 Flash (with self-healing loop).
    3. Combines results into ScenarioReport.
    4. Includes graceful fallback logic to guarantee the API never returns a 500 error.
    """
    logger.info(f"Starting scenario simulation '{params.scenario_id}' for corridor '{params.corridor_name}'.")

    # Step 1: Calculate quantitative physical metrics
    metrics = calculate_scenario_metrics(params)

    # Step 2: Generate LLM narrative synthesis with fallback safety net
    try:
        # Run synchronous Gemini call in thread pool to maintain async non-blocking execution
        narrative = await asyncio.to_thread(generate_scenario_narrative, params, metrics)
    except Exception as e:
        logger.error(f"Fallback triggered for scenario '{params.scenario_id}' due to LLM error: {str(e)}")
        # Controlled fallback narrative payload ensuring API zero-downtime resilience
        narrative = {
            "executive_briefing": (
                f"A {params.closure_percentage}% closure of the {params.corridor_name} over {params.duration_days} days "
                f"creates a daily deficit of {metrics.daily_deficit_mbpd} mbpd. National Strategic Petroleum Reserves provide "
                f"{metrics.spr_remaining_days_cover:.1f} days of remaining buffer against a {metrics.refinery_capacity_impact_pct:.1f}% drop in refinery utilization."
            ),
            "cascading_impacts": [
                f"Crude supply deficit of {metrics.daily_deficit_mbpd} mbpd directly constraining national refinery throughput.",
                f"Anticipated global Brent crude price spike of {metrics.estimated_brent_surge_pct}%, widening current account deficit.",
                f"Domestic fuel retail prices projected to surge by {metrics.estimated_domestic_fuel_price_surge_pct}%.",
                f"Macroeconomic GDP drag estimated at {metrics.macro_gdp_drag_pct}% due to elevated industrial energy costs.",
                "Increased freight tariffs and supply chain delays across domestic logistics networks."
            ],
            "recommended_policy_directives": [
                "Authorize immediate Strategic Petroleum Reserve (SPR) drawdown of up to 1.2 mbpd.",
                "Contract alternative spot crude cargoes from West African and Latin American producers.",
                "Direct Indian refiners (IOCL, BPCL, HPCL) to maximize middle distillate output and rationalize non-essential exports.",
                "Implement diplomatic and maritime security coordination to restore corridor navigation."
            ]
        }

    timestamp = datetime.now(timezone.utc).isoformat()

    report = ScenarioReport(
        scenario_id=params.scenario_id,
        corridor_name=params.corridor_name,
        closure_percentage=params.closure_percentage,
        duration_days=params.duration_days,
        metrics=metrics,
        executive_briefing=narrative["executive_briefing"],
        cascading_impacts=narrative["cascading_impacts"],
        recommended_policy_directives=narrative["recommended_policy_directives"],
        simulation_timestamp=timestamp
    )

    logger.info(f"Scenario simulation '{params.scenario_id}' completed successfully.")
    return report
