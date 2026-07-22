import asyncio
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.agents.scenario import run_scenario_simulation, ScenarioInput, ScenarioReport
from backend.app.agents.procurement import (
    run_procurement_orchestrator,
    RefineryRequirement,
    ProcurementRecommendationReport,
    OptimizationResult
)
from backend.app.agents.spr import run_spr_optimiser, SPRStatusInput, SPRPolicyReport
from backend.app.database import persist_scenario_execution_log, cache_threat_score
from backend.app.utils.scrapers import fetch_phase1_raw_payloads
from backend.app.agents.geopolitical import analyze_geopolitical_risk
from backend.app.models.schema import IngestionAnalysisResult

app = FastAPI(
    title="Argos Resilience API",
    description="Unified API for maritime disruption scenarios, procurement optimization, and Strategic Petroleum Reserve drawdown coordination."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Unified Response Model
class FullResilienceReport(BaseModel):
    scenario: ScenarioReport
    procurement: ProcurementRecommendationReport
    spr: SPRPolicyReport

@app.get("/")
def ping():
    return {"pong"}

@app.post("/api/scenarios/run-full-analysis", response_model=FullResilienceReport)
async def run_full_analysis(
    scenario_input: ScenarioInput,
    refinery_name: str = Query(
        default="Jamnagar & IOCL Complex",
        description="Target refinery name for crude procurement analysis"
    ),
    min_api_gravity: float = Query(
        default=28.0,
        description="Minimum acceptable blended API gravity degree"
    ),
    max_sulfur_pct: float = Query(
        default=2.0,
        description="Maximum acceptable blended sulfur percentage"
    )
):
    """
    Executes the entire multi-agent resilience workflow in a single request.
    Runs Procurement and SPR Optimisation concurrently to minimize latency if a supply deficit is present.
    """
    try:
        # Step 1: Run Scenario Modeller to establish crude deficit
        scenario_report = await run_scenario_simulation(scenario_input)
        deficit_mbpd = scenario_report.metrics.daily_deficit_mbpd

        # Step 2: Prepare inputs for downstream agents
        spr_input = SPRStatusInput(
            scenario_id=scenario_input.scenario_id,
            daily_supply_deficit_mbpd=deficit_mbpd,
            estimated_crisis_duration_days=scenario_input.duration_days,
            total_spr_capacity_mb=scenario_input.spr_total_capacity_mb,
            current_spr_stock_mb=scenario_input.spr_current_stock_mb
        )

        # Step 3: Run Procurement & SPR Agents concurrently using asyncio.gather if a deficit exists
        if deficit_mbpd > 0.0:
            refinery_req = RefineryRequirement(
                refinery_name=refinery_name,
                target_deficit_mbpd=deficit_mbpd,
                min_api_gravity=min_api_gravity,
                max_sulfur_pct=max_sulfur_pct
            )
            
            procurement_report, spr_report = await asyncio.gather(
                run_procurement_orchestrator(scenario_input.scenario_id, refinery_req),
                run_spr_optimiser(spr_input)
            )
        else:
            # Bypass procurement optimization for zero-deficit scenarios
            spr_report = await run_spr_optimiser(spr_input)
            
            empty_optimization = OptimizationResult(
                allocations=[],
                total_procured_mbpd=0.0,
                unfilled_deficit_mbpd=0.0,
                total_daily_cost_usd=0.0,
                weighted_api_gravity=0.0,
                weighted_sulfur_pct=0.0,
                optimization_status="OPTIMAL"
            )
            
            procurement_report = ProcurementRecommendationReport(
                scenario_id=scenario_input.scenario_id,
                refinery_name=refinery_name,
                optimization=empty_optimization,
                executive_summary="No crude deficit detected. Procurement optimization bypassed.",
                actionable_steps=["No action required. Supply chain is fully supplied."],
                risk_tradeoffs=["No risks or trade-offs identified as there is no supply disruption."],
                timestamp=datetime.now(timezone.utc).isoformat()
            )

        report = FullResilienceReport(
            scenario=scenario_report,
            procurement=procurement_report,
            spr=spr_report
        )
        
        # Persist report execution log to Supabase
        persist_scenario_execution_log(report.model_dump())
        
        return report

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Full resilience pipeline execution failed: {str(e)}"
        )

@app.post("/api/pipeline/phase1", response_model=IngestionAnalysisResult)
async def run_phase1():
    """
    Executes Phase 1 scraping pipeline and runs the geopolitical analyzer.
    Caches parsed threat scores in the Supabase database.
    """
    try:
        payload = await fetch_phase1_raw_payloads()
        result = await analyze_geopolitical_risk(payload)
        
        # Cache the threat scores to the database
        for risk in result.corridor_risks:
            cache_threat_score(
                corridor_name=risk.corridor_name,
                risk_score=risk.risk_score,
                threat_level=risk.threat_level,
                primary_driver=risk.primary_driver
            )
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Phase 1 pipeline failed: {str(e)}"
        )

@app.post("/api/pipeline/simulate", response_model=ScenarioReport)
async def run_simulate(scenario_input: ScenarioInput):
    """
    Directly runs the disruption Scenario Modeller Agent with inputs.
    """
    try:
        return await run_scenario_simulation(scenario_input)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Scenario simulation failed: {str(e)}"
        )

@app.post("/api/pipeline/procurement", response_model=ProcurementRecommendationReport)
async def run_procurement(scenario_id: str, refinery_req: RefineryRequirement):
    """
    Directly runs the crude Procurement Orchestrator Agent.
    """
    try:
        return await run_procurement_orchestrator(scenario_id, refinery_req)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Procurement optimization failed: {str(e)}"
        )

@app.post("/api/pipeline/spr", response_model=SPRPolicyReport)
async def run_spr(spr_input: SPRStatusInput):
    """
    Directly runs the Strategic Petroleum Reserve (SPR) Optimiser Agent.
    """
    try:
        return await run_spr_optimiser(spr_input)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"SPR optimization failed: {str(e)}"
        )