# tests/test_finance.py
import pytest
from backend.app.utils.scrapper import fetch_fin_APINinjas

@pytest.mark.anyio
async def test_live_api_data_fetch():
    result = await fetch_fin_APINinjas()
    
    assert "error" not in result, f"API call failed with error: {result.get('error')}"

    assert "price" in result, "API response missing the 'price' field"
    assert "data" not in result, "Function returned empty fallback data instead of real API data"
    

    print(f"\nLive API Response Data: {result}")