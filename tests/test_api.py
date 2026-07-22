import os
import sys
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root workspace directory is in sys.path for backend imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.main import app

client = TestClient(app)
OUTPUT_DIR = BASE_DIR / "agent_outputs"

@pytest.fixture(scope="module", autouse=True)
def setup_output_dir():
    """Ensure agent_outputs directory exists before running tests."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def test_ping():
    response = client.get("/")
    assert response.status_code == 200
    assert "pong" in response.json()


def test_full_analysis_success():
    """
    Test the full analysis endpoint with a valid disruption scenario.
    Verify scenario, procurement, and spr sections are populated and correct.
    Dumps output payload to agent_outputs/api_full_analysis_output.json
    """
    payload = {
        "scenario_id": "SIM-API-TEST-001",
        "corridor_name": "Strait of Hormuz",
        "closure_percentage": 50.0,
        "duration_days": 10,
        "baseline_india_imports_mbpd": 5.0,
        "corridor_baseline_mbpd": 2.2,
        "spr_total_capacity_mb": 40.0,
        "spr_current_stock_mb": 35.0
    }
    
    response = client.post("/api/scenarios/run-full-analysis", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    
    # Dump execution output payload to file
    output_file = OUTPUT_DIR / "api_full_analysis_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        
    assert "scenario" in data
    assert "procurement" in data
    assert "spr" in data
    
    # Verify scenario
    scenario = data["scenario"]
    assert scenario["scenario_id"] == "SIM-API-TEST-001"
    assert scenario["metrics"]["daily_deficit_mbpd"] == 1.1  # 2.2 * 50%
    
    # Verify procurement
    procurement = data["procurement"]
    assert procurement["scenario_id"] == "SIM-API-TEST-001"
    assert procurement["refinery_name"] == "Jamnagar & IOCL Complex"  # default value
    assert procurement["optimization"]["total_procured_mbpd"] > 0.0
    
    # Verify spr
    spr = data["spr"]
    assert spr["scenario_id"] == "SIM-API-TEST-001"
    # Verify that the custom spr capacity was propagated down to the spr optimiser input
    assert len(spr["optimization"]["daily_schedule"]) == 10


def test_full_analysis_zero_deficit():
    """
    Test that a zero deficit scenario (e.g. 0% closure) handles gracefully,
    bypassing linear programming optimization to avoid Pydantic ValidationError.
    """
    payload = {
        "scenario_id": "SIM-API-TEST-002",
        "corridor_name": "Strait of Hormuz",
        "closure_percentage": 0.0,
        "duration_days": 5,
        "baseline_india_imports_mbpd": 5.0,
        "corridor_baseline_mbpd": 2.2,
        "spr_total_capacity_mb": 39.5,
        "spr_current_stock_mb": 30.0
    }
    
    response = client.post("/api/scenarios/run-full-analysis", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["scenario"]["metrics"]["daily_deficit_mbpd"] == 0.0
    
    procurement = data["procurement"]
    assert procurement["optimization"]["total_procured_mbpd"] == 0.0
    assert "bypassed" in procurement["executive_summary"].lower()
    
    spr = data["spr"]
    assert spr["optimization"]["total_drawn_mb"] == 0.0


def test_full_analysis_query_overrides():
    """
    Test overriding refinery parameters via query variables.
    """
    payload = {
        "scenario_id": "SIM-API-TEST-003",
        "corridor_name": "Red Sea",
        "closure_percentage": 40.0,
        "duration_days": 7,
        "baseline_india_imports_mbpd": 5.0,
        "corridor_baseline_mbpd": 1.5,
        "spr_total_capacity_mb": 39.5,
        "spr_current_stock_mb": 30.0
    }
    
    # Override refinery parameters
    params = {
        "refinery_name": "IOCL Paradip Refinery",
        "min_api_gravity": 32.5,
        "max_sulfur_pct": 1.2
    }
    
    response = client.post(
        "/api/scenarios/run-full-analysis",
        json=payload,
        params=params
    )
    assert response.status_code == 200
    
    data = response.json()
    procurement = data["procurement"]
    assert procurement["refinery_name"] == "IOCL Paradip Refinery"
    # Ensure the optimized blend meets or reports correct metrics
    assert procurement["optimization"]["weighted_api_gravity"] >= 0.0


def test_pipeline_phase1_endpoint():
    """
    Test individual phase 1 scraping and analysis endpoint.
    Dumps output payload to agent_outputs/api_phase1_output.json
    """
    response = client.post("/api/pipeline/phase1")
    assert response.status_code == 200
    
    data = response.json()
    assert "overall_disruption_index" in data
    assert "corridor_risks" in data
    assert "executive_summary" in data
    
    # Dump execution output payload to file
    output_file = OUTPUT_DIR / "api_phase1_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def test_pipeline_simulate_endpoint():
    """
    Test individual simulate endpoint.
    Dumps output payload to agent_outputs/api_simulate_output.json
    """
    payload = {
        "scenario_id": "SIM-API-SIM-001",
        "corridor_name": "Strait of Hormuz",
        "closure_percentage": 50.0,
        "duration_days": 10,
        "baseline_india_imports_mbpd": 5.0,
        "corridor_baseline_mbpd": 2.2,
        "spr_total_capacity_mb": 40.0,
        "spr_current_stock_mb": 35.0
    }
    
    response = client.post("/api/pipeline/simulate", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["scenario_id"] == "SIM-API-SIM-001"
    assert "metrics" in data
    assert data["metrics"]["daily_deficit_mbpd"] == 1.1
    
    # Dump execution output payload to file
    output_file = OUTPUT_DIR / "api_simulate_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def test_pipeline_procurement_endpoint():
    """
    Test individual procurement endpoint.
    Dumps output payload to agent_outputs/api_procurement_output.json
    """
    refinery_req = {
        "refinery_name": "IOCL Paradip Refinery",
        "target_deficit_mbpd": 1.2,
        "min_api_gravity": 31.0,
        "max_sulfur_pct": 1.0
    }
    
    response = client.post(
        "/api/pipeline/procurement",
        json=refinery_req,
        params={"scenario_id": "SIM-API-PROC-001"}
    )
    assert response.status_code == 200
    
    data = response.json()
    assert data["scenario_id"] == "SIM-API-PROC-001"
    assert data["refinery_name"] == "IOCL Paradip Refinery"
    assert "optimization" in data
    
    # Dump execution output payload to file
    output_file = OUTPUT_DIR / "api_procurement_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def test_pipeline_spr_endpoint():
    """
    Test individual spr endpoint.
    Dumps output payload to agent_outputs/api_spr_output.json
    """
    spr_input = {
        "scenario_id": "SIM-API-SPR-001",
        "daily_supply_deficit_mbpd": 1.1,
        "estimated_crisis_duration_days": 15,
        "total_spr_capacity_mb": 39.5,
        "current_spr_stock_mb": 30.0,
        "max_daily_discharge_rate_mbpd": 1.2,
        "strategic_floor_pct": 25.0
    }
    
    response = client.post("/api/pipeline/spr", json=spr_input)
    assert response.status_code == 200
    
    data = response.json()
    assert data["scenario_id"] == "SIM-API-SPR-001"
    assert "optimization" in data
    assert len(data["optimization"]["daily_schedule"]) == 15
    
    # Dump execution output payload to file
    output_file = OUTPUT_DIR / "api_spr_output.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

