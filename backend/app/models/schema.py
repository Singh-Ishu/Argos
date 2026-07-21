from pydantic import BaseModel, Field
from typing import List, Optional

class CorridorRisk(BaseModel):
    corridor_name: str = Field(description="Name of maritime corridor e.g., 'Strait of Hormuz', 'Red Sea'")
    risk_score: float = Field(description="Disruption probability from 0.0 (Safe) to 1.0 (Blocked)")
    threat_level: str = Field(description="Category: LOW, MEDIUM, HIGH, CRITICAL")
    primary_driver: str = Field(description="Primary cause e.g., 'Military Skirmish', 'Sanction Increase'")

class IngestionAnalysisResult(BaseModel):
    overall_disruption_index: float = Field(description="Global supply chain stress index (0-100)")
    corridor_risks: List[CorridorRisk]
    executive_summary: str = Field(description="Concise 2-sentence situational briefing")
    actionable_alerts: List[str] = Field(description="List of critical triggers for downstream orchestration")