import asyncio
import json
import httpx 
from typing import Dict, Any 
from backend.app.config import settings
from fastapi import HTTPException
from datetime import datetime, timedelta

#Scrape information from APIs to the following categories:
# Finances & Commodities (API Ninjas: Commodity Price API / US EIA API)
# Geopolitical & Security Signals (ACLED API / GDELT Project)
# Maritimes & Shipping Logistics (AISstream.io / VesselAPI / JSONCargoAPI)
# Miscellaneous (Aljazeera or some newsoutlet / FRED API)

async def fetch_fin_APINinjas():
    UNIT : str = "liter"
    CURRENCY : str = "INR"
    url = f"https://api.api-ninjas.com/v1/commodityprice?name=crude_oil&currency={CURRENCY}&unit={UNIT}"
    API_KEY = settings.API_NINJAS_KEY
    headers = {"X-Api-Key": settings.API_NINJAS_KEY}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": f"Ninja API feed failed: {str(e)}", "data": {}}

async def fetch_fin_EIA():
    api_key = settings.EIA_API_KEY
    url = f"https://api.eia.gov/v2/crude-oil-imports/data/?api_key={api_key}"
    x_params = {
        "frequency": "monthly",
        "data": ["quantity"],
        "facets": {},
        "start": None,
        "end": None,
        "sort": [
            {
                "column": "period",
                "direction": "desc"
            }
        ],
        "offset": 0,
        "length": 5000
    }
    headers = {
        "X-Params": json.dumps(x_params)
    }
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": f"EIA API feed failed: {str(e)}", "data": {}}

async def fetch_geopol_acled(limit: int = 5000, page: int = 1) -> Dict[str, Any]:
    """
    Fetches the past week's worth of actions/events from ACLED API.
    Uses OAuth token authentication as described in the documentation.
    """
    if not settings.ACLED_EMAIL or not settings.ACLED_PASSWORD:
        return {"error": "ACLED API feed failed: Credentials not configured", "data": []}

    token_url = "https://acleddata.com/oauth/token"
    token_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    token_data = {
        "username": settings.ACLED_EMAIL,
        "password": settings.ACLED_PASSWORD,
        "grant_type": "password",
        "client_id": "acled",
        "scope": "authenticated"
    }

    try:
        async with httpx.AsyncClient() as client:
            # 1. Authenticate to get OAuth access token
            token_response = await client.post(
                token_url,
                headers=token_headers,
                data=token_data,
                timeout=10.0
            )
            token_response.raise_for_status()
            token_res_json = token_response.json()
            access_token = token_res_json.get("access_token")
            if not access_token:
                return {"error": "ACLED API feed failed: Access token not found in response", "data": []}

            # 2. Query ACLED data for the past week
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=7)
            
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            api_url = "https://acleddata.com/api/acled/read?_format=json"
            params = {
                "event_date": f"{start_str}|{end_str}",
                "event_date_where": "BETWEEN",
                "limit": limit,
                "page": page
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            data_response = await client.get(
                api_url,
                params=params,
                headers=headers,
                timeout=15.0
            )
            data_response.raise_for_status()
            return data_response.json()

    except Exception as e:
        return {"error": f"ACLED API feed failed: {str(e)}", "data": []}