import asyncio
import json
from google import genai
from google.genai import types
from typing import Dict, Any, Optional
from backend.app.config import settings
from backend.app.models.schema import IngestionAnalysisResult
from backend.app.utils.scrapper import fetch_fin_APINinjas, fetch_fin_EIA

# Initialize the Gemini Client
client = genai.Client(api_key=settings.GEMINI_API_KEY)

SYSTEM_INSTRUCTION = """
You are the Geopolitical Risk Agent for Argos, an energy supply chain resilience platform.
Your task is to analyze raw heterogeneous data payloads (commodity prices, news/military signals, shipping status)
and evaluate supply chain disruption risks for critical oil transportation corridors servicing India.

Rules:
1. Synthesize all provided data feeds into a unified risk assessment.
2. Ensure risk scores reflect real-time threat escalations accurately.
3. Be objective, precise, and devoid of speculative fluff.
"""

async def analyze_geopolitical_risk(payload_manifest: Optional[Dict[str, Any]] = None) -> IngestionAnalysisResult:
    """
    Passes raw ingestion payloads to Gemini 2.5 Flash for structured risk analysis.
    If payload_manifest is not provided, fetches live data from the commodity/finance scraper endpoints.
    """
    if payload_manifest is None:
        ninja_data, eia_data = await asyncio.gather(
            fetch_fin_APINinjas(),
            fetch_fin_EIA()
        )
        payload_manifest = {
            "finances": {
                "api_ninjas": ninja_data,
                "eia": eia_data
            },
            "geopolitical": {},
            "shipping": {}
        }
    prompt = f"""
    Analyze the following incoming raw data feeds:

    --- COMMODITY & FINANCE DATA ---
    {json.dumps(payload_manifest.get('finances', {}))}

    --- GEOPOLITICAL & SECURITY NEWS ---
    {json.dumps(payload_manifest.get('geopolitical', {}))}

    --- MARITIME & SHIPPING METRICS ---
    {json.dumps(payload_manifest.get('shipping', {}))}

    Generate a structured risk assessment based strictly on this data.
    """

    def _sync_call():
        return client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=IngestionAnalysisResult,
                temperature=0.2, # Low temperature for consistent deterministic scoring
            )
        )

    try:
        response = await asyncio.to_thread(_sync_call)
        
        # Parse output directly into Pydantic model
        result = IngestionAnalysisResult.model_validate_json(response.text)
        return result

    except Exception as e:
        # Fallback response in case of API failure or parsing errors
        return IngestionAnalysisResult(
            overall_disruption_index=0.0,
            corridor_risks=[],
            executive_summary=f"Analysis pipeline error: {str(e)}",
            actionable_alerts=["ALERT: Risk agent execution failed. Falling back to cached state."]
        )