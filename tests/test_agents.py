import os
import sys
import json
import pytest
from pathlib import Path

# Ensure root workspace directory is in sys.path for backend imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.agents.geopolitical import analyze_geopolitical_risk
from backend.app.models.schema import IngestionAnalysisResult

from backend.app.agents.scenario import (
    ScenarioInput,
    ScenarioReport,
    run_scenario_simulation
)

from backend.app.agents.spr import (
    SPRStatusInput,
    SPRPolicyReport,
    run_spr_optimiser
)

from backend.app.agents.procurement import (
    RefineryRequirement,
    CrudeOption,
    ProcurementRecommendationReport,
    run_procurement_orchestrator
)

OUTPUT_DIR = BASE_DIR / "agent_outputs"


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture(scope="session", autouse=True)
def setup_output_dir():
    """Ensure agent_outputs directory exists before running tests."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@pytest.mark.anyio
async def test_geopolitical_agent_with_mock_ingestion():
    """
    Unit test for Geopolitical Risk Agent using mock ingestion payload.
    Logs output to agent_outputs/geopolitical_agent_output.txt
    """
    mock_payload = {
        "finances": {
            "api_ninjas": {
                "brent_crude": {"price": 84.50, "currency": "USD"},
                "wti_crude": {"price": 79.80, "currency": "USD"}
            },
            "eia": {
                "us_crude_stocks": 420.5,
                "weekly_change_mb": -2.3
            }
        },
        "geopolitical": {
            "news": [
                "Naval escort vessel deployed to Strait of Hormuz amidst rising regional tensions.",
                "Drone attack reported near Bab-el-Mandeb; tanker rerouting increases transit times by 12 days."
            ]
        },
        "shipping": {
            "strait_of_hormuz_transit_status": "RESTRICTED",
            "bab_el_mandeb_risk_level": "HIGH",
            "vessel_freight_rate_index": 240.5
        }
    }

    result = await analyze_geopolitical_risk(payload_manifest=mock_payload)

    assert isinstance(result, IngestionAnalysisResult), f"Expected IngestionAnalysisResult, got {type(result)}"
    assert result.executive_summary != "", "Executive summary should not be empty"

    output_file = OUTPUT_DIR / "geopolitical_agent_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=================================================================\n")
        f.write("             ARGOS GEOPOLITICAL RISK AGENT OUTPUT                \n")
        f.write("=================================================================\n\n")
        f.write(f"Overall Disruption Index : {result.overall_disruption_index}\n\n")
        f.write(f"Executive Summary        :\n{result.executive_summary}\n\n")
        f.write("Corridor Risks          :\n")
        for risk in result.corridor_risks:
            f.write(f"  - {risk}\n")
        f.write("\nActionable Alerts       :\n")
        for alert in result.actionable_alerts:
            f.write(f"  - {alert}\n")
        f.write("\n=================================================================\n")
        f.write(f"Raw JSON Output:\n{json.dumps(result.model_dump(), indent=2)}\n")

    print(f"\n[SUCCESS] Geopolitical agent output logged to: {output_file}")


@pytest.mark.anyio
async def test_scenario_agent_with_mock_input():
    """
    Unit test for Disruption Scenario Modeller Agent using mock parameters.
    Logs output to agent_outputs/scenario_agent_output.txt
    """
    mock_input = ScenarioInput(
        scenario_id="SIM-HORMUZ-MOCK-001",
        corridor_name="Strait of Hormuz",
        closure_percentage=60.0,
        duration_days=30,
        baseline_india_imports_mbpd=5.0,
        corridor_baseline_mbpd=2.2,
        spr_total_capacity_mb=39.5,
        spr_current_stock_mb=30.0
    )

    report = await run_scenario_simulation(mock_input)

    assert isinstance(report, ScenarioReport), f"Expected ScenarioReport, got {type(report)}"
    assert report.scenario_id == "SIM-HORMUZ-MOCK-001"
    assert report.metrics.daily_deficit_mbpd > 0
    assert len(report.cascading_impacts) > 0

    output_file = OUTPUT_DIR / "scenario_agent_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=================================================================\n")
        f.write("         ARGOS DISRUPTION SCENARIO MODELLER AGENT OUTPUT        \n")
        f.write("=================================================================\n\n")
        f.write(f"Scenario ID             : {report.scenario_id}\n")
        f.write(f"Corridor Name           : {report.corridor_name}\n")
        f.write(f"Closure Percentage      : {report.closure_percentage}%\n")
        f.write(f"Disruption Duration     : {report.duration_days} days\n")
        f.write(f"Timestamp               : {report.simulation_timestamp}\n\n")
        f.write("--- Quantitative Metrics ---\n")
        f.write(f"Daily Deficit (mbpd)    : {report.metrics.daily_deficit_mbpd}\n")
        f.write(f"Total Volume Lost (mb)  : {report.metrics.total_volume_lost_mb}\n")
        f.write(f"Refinery Capacity Drop  : {report.metrics.refinery_capacity_impact_pct}%\n")
        f.write(f"SPR Depletion Days Used : {report.metrics.spr_depletion_days_used}\n")
        f.write(f"SPR Remaining Cover     : {report.metrics.spr_remaining_days_cover} days\n")
        f.write(f"Brent Crude Surge       : +{report.metrics.estimated_brent_surge_pct}%\n")
        f.write(f"Domestic Fuel Surge     : +{report.metrics.estimated_domestic_fuel_price_surge_pct}%\n")
        f.write(f"Macro GDP Drag          : -{report.metrics.macro_gdp_drag_pct}%\n\n")
        f.write(f"Executive Briefing      :\n{report.executive_briefing}\n\n")
        f.write("Cascading Impacts       :\n")
        for impact in report.cascading_impacts:
            f.write(f"  - {impact}\n")
        f.write("\nRecommended Policy Directives:\n")
        for directive in report.recommended_policy_directives:
            f.write(f"  - {directive}\n")
        f.write("\n=================================================================\n")
        f.write(f"Raw JSON Output:\n{json.dumps(report.model_dump(), indent=2)}\n")

    print(f"\n[SUCCESS] Scenario agent output logged to: {output_file}")


@pytest.mark.anyio
async def test_spr_agent_with_mock_input():
    """
    Unit test for Strategic Petroleum Reserve (SPR) Optimiser Agent using mock parameters.
    Logs output to agent_outputs/spr_agent_output.txt
    """
    mock_input = SPRStatusInput(
        scenario_id="SIM-SPR-MOCK-002",
        daily_supply_deficit_mbpd=1.1,
        estimated_crisis_duration_days=15,
        total_spr_capacity_mb=39.5,
        current_spr_stock_mb=30.0,
        max_daily_discharge_rate_mbpd=1.2,
        strategic_floor_pct=25.0
    )

    report = await run_spr_optimiser(mock_input)

    assert isinstance(report, SPRPolicyReport), f"Expected SPRPolicyReport, got {type(report)}"
    assert report.scenario_id == "SIM-SPR-MOCK-002"
    assert len(report.optimization.daily_schedule) == 15
    assert report.optimization.alert_level in ["GREEN", "AMBER", "RED", "CRITICAL_DEFENSE_RESERVE_ONLY"]

    output_file = OUTPUT_DIR / "spr_agent_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=================================================================\n")
        f.write("           ARGOS STRATEGIC PETROLEUM RESERVE AGENT OUTPUT        \n")
        f.write("=================================================================\n\n")
        f.write(f"Scenario ID             : {report.scenario_id}\n")
        f.write(f"Alert Level             : {report.optimization.alert_level}\n")
        f.write(f"Total Drawn (mb)        : {report.optimization.total_drawn_mb}\n")
        f.write(f"Final Stock (mb)        : {report.optimization.final_remaining_stock_mb}\n")
        f.write(f"Average Daily Release   : {report.optimization.average_daily_release_mbpd} mbpd\n")
        f.write(f"Floor Breached          : {report.optimization.floor_breached}\n")
        f.write(f"Replenishment Start Day : Day {report.optimization.recommended_replenishment_start_day}\n")
        f.write(f"Timestamp               : {report.timestamp}\n\n")
        f.write("--- Daily Drawdown Schedule ---\n")
        for day_sched in report.optimization.daily_schedule:
            f.write(f"  Day {day_sched.day:02d}: Release={day_sched.drawdown_volume_mbpd:.2f} mbpd, Stock={day_sched.remaining_stock_mb:.2f} mb ({day_sched.stock_capacity_pct:.1f}%), Runway={day_sched.days_of_runway_left:.1f} days\n")
        f.write(f"\nPolicy Briefing:\n{report.policy_briefing}\n\n")
        f.write("Inter-Agency Action Directives:\n")
        for action in report.inter_agency_actions:
            f.write(f"  - {action}\n")
        f.write(f"\nReplenishment Strategy:\n{report.replenishment_strategy}\n")
        f.write("\n=================================================================\n")
        f.write(f"Raw JSON Output:\n{json.dumps(report.model_dump(), indent=2)}\n")

    print(f"\n[SUCCESS] SPR agent output logged to: {output_file}")


@pytest.mark.anyio
async def test_procurement_agent_with_mock_input():
    """
    Unit test for Adaptive Procurement Orchestrator Agent using mock inputs.
    Logs output to agent_outputs/procurement_agent_output.txt
    """
    refinery_req = RefineryRequirement(
        refinery_name="IOCL Paradip Refinery",
        target_deficit_mbpd=1.2,
        min_api_gravity=31.0,
        max_sulfur_pct=1.0
    )

    candidate_crudes = [
        CrudeOption(
            crude_name="Basrah Medium",
            origin_country="Iraq",
            api_gravity=29.0,
            sulfur_pct=2.50,
            spot_price_usd_bbl=76.50,
            freight_risk_premium_usd_bbl=3.20,
            max_availability_mbpd=0.8,
            lead_time_days=12
        ),
        CrudeOption(
            crude_name="West African Forcados",
            origin_country="Nigeria",
            api_gravity=34.5,
            sulfur_pct=0.20,
            spot_price_usd_bbl=82.00,
            freight_risk_premium_usd_bbl=4.50,
            max_availability_mbpd=0.5,
            lead_time_days=18
        ),
        CrudeOption(
            crude_name="Brazilian Tupi",
            origin_country="Brazil",
            api_gravity=30.2,
            sulfur_pct=0.40,
            spot_price_usd_bbl=80.00,
            freight_risk_premium_usd_bbl=5.80,
            max_availability_mbpd=0.6,
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
        )
    ]

    report = await run_procurement_orchestrator(
        scenario_id="SIM-PROCUREMENT-MOCK-003",
        refinery_req=refinery_req,
        candidate_crudes=candidate_crudes
    )

    assert isinstance(report, ProcurementRecommendationReport), f"Expected ProcurementRecommendationReport, got {type(report)}"
    assert report.refinery_name == "IOCL Paradip Refinery"
    assert report.optimization.total_procured_mbpd > 0

    output_file = OUTPUT_DIR / "procurement_agent_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=================================================================\n")
        f.write("       ARGOS ADAPTIVE PROCUREMENT ORCHESTRATOR AGENT OUTPUT       \n")
        f.write("=================================================================\n\n")
        f.write(f"Scenario ID             : {report.scenario_id}\n")
        f.write(f"Refinery Name           : {report.refinery_name}\n")
        f.write(f"Optimization Status     : {report.optimization.optimization_status}\n")
        f.write(f"Total Procured (mbpd)   : {report.optimization.total_procured_mbpd}\n")
        f.write(f"Unfilled Deficit (mbpd) : {report.optimization.unfilled_deficit_mbpd}\n")
        f.write(f"Total Daily Cost ($USD) : ${report.optimization.total_daily_cost_usd:,.2f}\n")
        f.write(f"Weighted API Gravity    : {report.optimization.weighted_api_gravity}\n")
        f.write(f"Weighted Sulfur %       : {report.optimization.weighted_sulfur_pct}%\n")
        f.write(f"Timestamp               : {report.timestamp}\n\n")
        f.write("--- Selected Crude Allocations ---\n")
        for alloc in report.optimization.allocations:
            f.write(f"  - {alloc.crude_name} ({alloc.origin_country}): {alloc.allocated_mbpd:.2f} mbpd @ ${alloc.total_landed_cost_usd_bbl:.2f}/bbl (Lead time: {alloc.lead_time_days} days)\n")
        f.write(f"\nExecutive Summary:\n{report.executive_summary}\n\n")
        f.write("Actionable Procurement Steps:\n")
        for step in report.actionable_steps:
            f.write(f"  - {step}\n")
        f.write("\nRisk Trade-offs & Compromises:\n")
        for tradeoff in report.risk_tradeoffs:
            f.write(f"  - {tradeoff}\n")
        f.write("\n=================================================================\n")
        f.write(f"Raw JSON Output:\n{json.dumps(report.model_dump(), indent=2)}\n")

    print(f"\n[SUCCESS] Procurement agent output logged to: {output_file}")
