import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from supabase import create_client, Client
from backend.app.config import settings

logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_client: Optional[Client] = None

if settings.SUPABASE_URL and settings.SUPABASE_KEY and "placeholder" not in settings.SUPABASE_URL:
    try:
        supabase_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
else:
    logger.warning("Supabase URL or Key missing / using placeholder. Client not initialized.")


def verify_database_tables() -> Dict[str, Any]:
    """
    Verifies connection to Supabase and queries table existence.
    Used by start.py script to perform pre-flight checks.
    """
    status = {
        "client_connected": False,
        "scenario_execution_logs_exists": False,
        "cached_threat_scores_exists": False,
        "error": None
    }
    
    if not supabase_client:
        status["error"] = "Supabase client is not initialized (missing or invalid credentials)."
        return status
        
    status["client_connected"] = True
    
    # Check scenario_execution_logs table
    try:
        supabase_client.table("scenario_execution_logs").select("id").limit(1).execute()
        status["scenario_execution_logs_exists"] = True
    except Exception as e:
        logger.debug(f"Verification query for scenario_execution_logs failed: {e}")
        
    # Check cached_threat_scores table
    try:
        supabase_client.table("cached_threat_scores").select("id").limit(1).execute()
        status["cached_threat_scores_exists"] = True
    except Exception as e:
        logger.debug(f"Verification query for cached_threat_scores failed: {e}")
        
    return status


def persist_scenario_execution_log(log_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Persists a scenario execution log to scenario_execution_logs table in Supabase.
    Gracefully catches and logs errors to prevent API crash.
    """
    if not supabase_client:
        logger.warning("Supabase client not initialized. Skipping execution log persistence.")
        return None
        
    try:
        scenario = log_data.get("scenario", {})
        if not scenario:
            logger.warning("No scenario sub-report found in log data.")
            return None
            
        row = {
            "scenario_id": scenario.get("scenario_id"),
            "corridor_name": scenario.get("corridor_name"),
            "closure_percentage": float(scenario.get("closure_percentage", 0.0)),
            "duration_days": int(scenario.get("duration_days", 0)),
            "metrics": scenario.get("metrics"),
            "executive_briefing": scenario.get("executive_briefing"),
            "cascading_impacts": scenario.get("cascading_impacts"),
            "recommended_policy_directives": scenario.get("recommended_policy_directives"),
            "simulation_timestamp": scenario.get("simulation_timestamp", datetime.now(timezone.utc).isoformat()),
        }
        
        result = supabase_client.table("scenario_execution_logs").insert(row).execute()
        logger.info(f"Successfully persisted scenario log for '{row['scenario_id']}' to Supabase.")
        return result.data
    except Exception as e:
        logger.warning(f"Graceful degradation: Failed to persist scenario log to database: {e}")
        return None


def cache_threat_score(corridor_name: str, risk_score: float, threat_level: str, primary_driver: str) -> Optional[Dict[str, Any]]:
    """
    Upserts threat scores into cached_threat_scores table.
    Gracefully catches and logs errors.
    """
    if not supabase_client:
        logger.warning("Supabase client not initialized. Skipping threat score cache.")
        return None
        
    try:
        row = {
            "corridor_name": corridor_name,
            "risk_score": float(risk_score),
            "threat_level": threat_level,
            "primary_driver": primary_driver,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        result = supabase_client.table("cached_threat_scores").upsert(row, on_conflict="corridor_name").execute()
        logger.info(f"Successfully cached threat score for '{corridor_name}' in Supabase.")
        return result.data
    except Exception as e:
        logger.warning(f"Graceful degradation: Failed to cache threat score to database: {e}")
        return None
