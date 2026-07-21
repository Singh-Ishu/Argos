import pytest
from backend.app.agents.geopolitical import analyze_geopolitical_risk
from backend.app.models.schema import IngestionAnalysisResult

@pytest.mark.anyio
async def test_live_geopolitical_agent():
    """
    Test the geopolitical risk agent against live scraper endpoints (API Ninjas & EIA)
    and output the structured response.
    """
    result = await analyze_geopolitical_risk()

    # Verify that a valid IngestionAnalysisResult model was returned
    assert isinstance(result, IngestionAnalysisResult), f"Expected IngestionAnalysisResult, got {type(result)}"
    assert result.executive_summary != "", "Executive summary should not be empty"

    # Print out the detailed response as requested
    print("\n================ LIVE GEOPOLITICAL AGENT RESPONSE ================")
    print(f"Overall Disruption Index : {result.overall_disruption_index}")
    print(f"Executive Summary        : {result.executive_summary}")
    print(f"Corridor Risks          : {result.corridor_risks}")
    print(f"Actionable Alerts       : {result.actionable_alerts}")
    print("==================================================================")
