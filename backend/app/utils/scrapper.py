import asyncio
import httpx 
from typing import Dict, Any 
from backend.app.config import settings
from fastapi import HTTPException

#Scrape information from APIs to the following categories:
# Finances & Commodities (API Ninjas / Commodity Price API / US EIA API)
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
        return {"error": f"Finance feed failed: {str(e)}", "data": {}}