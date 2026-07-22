import os
import pytest
from backend.app.utils.scrapers import fetch_maritime_data
from backend.app.config import settings

@pytest.mark.anyio
async def test_live_vessel_api_fetch():
    """
    Live integration check for VesselAPI endpoint.
    This will query the live VesselAPI exactly once.
    """
    if not settings.VESSELAPI_API_KEY or "placeholder" in settings.VESSELAPI_API_KEY:
        pytest.skip("VESSELAPI_API_KEY is not configured in .env. Skipping live test.")
        
    # Override environment variable to bypass the pytest query-saving guard
    os.environ["RUN_LIVE_VESSEL_TEST"] = "true"
    
    try:
        result = await fetch_maritime_data()
        
        # Verify the API response
        assert "error" not in result, f"Live VesselAPI query failed with error: {result.get('error')}"
        assert "vessels_sample" in result, "VesselAPI did not return live vessel details."
        
        sample = result["vessels_sample"]
        assert sample is not None
        assert "count" in sample
        assert "first_vessel_name" in sample
        
        print(f"\n[LIVE INTEGRATION SUCCESS] VesselAPI Response: {result}")
        
    finally:
        # Clean up override so subsequent tests do not trigger live calls
        os.environ.pop("RUN_LIVE_VESSEL_TEST", None)
