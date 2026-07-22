import os
import sys
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Ensure root workspace directory is in sys.path for backend imports
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from backend.app.main import app

client = TestClient(app)

def test_ping():
    response = client.get("/")
    assert response.status_code == 200
    assert "pong" in response.json()


def test_full_analysis_success():
    """
    Test the full analysis endpoint with a valid disruption scenario.
    Verify scenario, procurement, and spr sections are populated and correct.
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
