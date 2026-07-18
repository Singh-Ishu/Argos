import pytest
import json
from unittest.mock import MagicMock, patch
from backend.app.utils.scrapper import fetch_geopol_acled
from backend.app.config import settings

@pytest.mark.anyio
async def test_fetch_geopol_acled_success():
    # Arrange
    # Mock token response
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {
        "access_token": "fake_token_123",
        "token_type": "Bearer",
        "expires_in": 86400
    }
    mock_token_resp.raise_for_status = MagicMock()

    # Mock data response
    mock_data_resp = MagicMock()
    mock_data_resp.status_code = 200
    mock_data_resp.json.return_value = {
        "status": 200,
        "count": 2,
        "data": [
            {"event_id_cnty": "GEO1", "event_date": "2026-07-15", "event_type": "Protests"},
            {"event_id_cnty": "GEO2", "event_date": "2026-07-16", "event_type": "Riots"}
        ]
    }
    mock_data_resp.raise_for_status = MagicMock()

    # Patch settings to have credentials
    with patch.object(settings, "ACLED_EMAIL", "test@example.com"), \
         patch.object(settings, "ACLED_PASSWORD", "secret123"):
         
        with patch("httpx.AsyncClient.post", return_value=mock_token_resp) as mock_post, \
             patch("httpx.AsyncClient.get", return_value=mock_data_resp) as mock_get:
             
            # Act
            result = await fetch_geopol_acled()
            
            # Assert
            assert "error" not in result
            assert result["status"] == 200
            assert len(result["data"]) == 2
            assert result["data"][0]["event_id_cnty"] == "GEO1"
            
            # Verify calls
            mock_post.assert_called_once()
            called_token_url = mock_post.call_args[0][0]
            called_token_data = mock_post.call_args[1].get("data", {})
            assert "oauth/token" in called_token_url
            assert called_token_data["username"] == "test@example.com"
            assert called_token_data["password"] == "secret123"
            
            mock_get.assert_called_once()
            called_api_url = mock_get.call_args[0][0]
            called_params = mock_get.call_args[1].get("params", {})
            called_headers = mock_get.call_args[1].get("headers", {})
            assert "api/acled/read" in called_api_url
            assert called_params["event_date_where"] == "BETWEEN"
            assert "Authorization" in called_headers
            assert called_headers["Authorization"] == "Bearer fake_token_123"

@pytest.mark.anyio
async def test_fetch_geopol_acled_missing_credentials():
    # Arrange: ensure credentials are blank
    with patch.object(settings, "ACLED_EMAIL", ""), \
         patch.object(settings, "ACLED_PASSWORD", ""):
         
        # Act
        result = await fetch_geopol_acled()
        
        # Assert
        assert "error" in result
        assert "Credentials not configured" in result["error"]

@pytest.mark.anyio
async def test_fetch_geopol_acled_token_failure():
    # Arrange
    with patch.object(settings, "ACLED_EMAIL", "test@example.com"), \
         patch.object(settings, "ACLED_PASSWORD", "secret123"):
         
        with patch("httpx.AsyncClient.post", side_effect=Exception("OAuth server down")):
            # Act
            result = await fetch_geopol_acled()
            
            # Assert
            assert "error" in result
            assert "OAuth server down" in result["error"]

@pytest.mark.anyio
async def test_fetch_geopol_acled_data_failure():
    # Arrange
    mock_token_resp = MagicMock()
    mock_token_resp.status_code = 200
    mock_token_resp.json.return_value = {
        "access_token": "fake_token_123"
    }
    mock_token_resp.raise_for_status = MagicMock()

    with patch.object(settings, "ACLED_EMAIL", "test@example.com"), \
         patch.object(settings, "ACLED_PASSWORD", "secret123"):
         
        with patch("httpx.AsyncClient.post", return_value=mock_token_resp), \
             patch("httpx.AsyncClient.get", side_effect=Exception("API limit exceeded")):
             
            # Act
            result = await fetch_geopol_acled()
            
            # Assert
            assert "error" in result
            assert "API limit exceeded" in result["error"]

@pytest.mark.anyio
async def test_live_acled_api():
    # Act & Assert
    if not settings.ACLED_EMAIL or not settings.ACLED_PASSWORD:
        pytest.skip("ACLED credentials not configured, skipping live ACLED integration test")
        
    result = await fetch_geopol_acled()
    assert "error" not in result, f"Live ACLED API call failed with error: {result.get('error')}"
    assert "status" in result, "Live ACLED API response missing 'status' field"
    assert "data" in result, "Live ACLED API response missing 'data'"
    
    print(f"\nLive ACLED API Response: {result}")
