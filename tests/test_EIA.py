import pytest
import json
from unittest.mock import MagicMock, patch
from backend.app.utils.scrapers import fetch_fin_EIA
from backend.app.config import settings

@pytest.mark.anyio
async def test_fetch_fin_EIA_success():
    # Arrange
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "response": {
            "data": [
                {"quantity": 100, "period": "2026-01"}
            ]
        }
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.get", return_value=mock_response) as mock_get:
        # Act
        result = await fetch_fin_EIA()
        
        # Assert
        assert "error" not in result
        assert "response" in result
        assert result["response"]["data"][0]["quantity"] == 100
        
        # Verify call parameters
        mock_get.assert_called_once()
        called_url = mock_get.call_args[0][0]
        called_headers = mock_get.call_args[1].get("headers", {})
        
        assert "api.eia.gov/v2" in called_url
        assert "X-Params" in called_headers
        
        # Verify x_params content
        x_params = json.loads(called_headers["X-Params"])
        assert x_params["frequency"] == "monthly"
        assert "quantity" in x_params["data"]

@pytest.mark.anyio
async def test_fetch_fin_EIA_failure():
    # Arrange
    with patch("httpx.AsyncClient.get", side_effect=Exception("Connection timed out")):
        # Act
        result = await fetch_fin_EIA()
        
        # Assert
        assert "error" in result
        assert "EIA API feed failed: Connection timed out" in result["error"]

@pytest.mark.anyio
async def test_live_EIA_api():
    # Act & Assert
    if not settings.EIA_API_KEY:
        pytest.skip("EIA_API_KEY not configured, skipping live EIA integration test")
        
    result = await fetch_fin_EIA()
    assert "error" not in result, f"Live EIA API call failed with error: {result.get('error')}"
    assert "response" in result, "Live EIA API response missing 'response' object"
    assert "data" in result["response"], "Live EIA API response missing 'data' in 'response'"
    
    print(f"\nLive EIA API Response Data: {result}")
