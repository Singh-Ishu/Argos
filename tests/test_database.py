import pytest
from backend.app.database import (
    verify_database_tables,
    supabase_client,
    persist_scenario_execution_log,
    cache_threat_score
)
from backend.app.config import settings

@pytest.mark.anyio
async def test_live_supabase_connection():
    """
    Test live database connection and table existence verification.
    Queries your live Supabase credentials to ensure connections succeed.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY or "placeholder" in settings.SUPABASE_URL:
        pytest.skip("Supabase URL or Key not configured. Skipping live connection test.")
        
    status = verify_database_tables()
    
    assert status["client_connected"] is True, f"Failed to connect to Supabase: {status['error']}"
    assert status["scenario_execution_logs_exists"] is True, (
        "Table 'scenario_execution_logs' not found in Supabase! "
        "Please run backend/schema.sql in your Supabase SQL editor."
    )
    assert status["cached_threat_scores_exists"] is True, (
        "Table 'cached_threat_scores' not found in Supabase! "
        "Please run backend/schema.sql in your Supabase SQL editor."
    )


@pytest.mark.anyio
async def test_live_supabase_write_and_delete_operations():
    """
    Test caching threat score (upsert), selecting, and deleting it on the live database.
    Verifies that write permissions are properly configured.
    """
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY or "placeholder" in settings.SUPABASE_URL:
        pytest.skip("Supabase URL or Key not configured. Skipping live database operations test.")
        
    test_corridor = "TEST_INTEGRATION_CORRIDOR_TEMP"
    
    # 1. Perform upsert (write cache)
    write_result = cache_threat_score(
        corridor_name=test_corridor,
        risk_score=0.99,
        threat_level="CRITICAL",
        primary_driver="automated-integration-check"
    )
    
    assert write_result is not None, "Failed to write to cached_threat_scores table (received None). Check database schema and RLS policies."
    
    # 2. Select entry to verify presence
    assert supabase_client is not None
    select_result = supabase_client.table("cached_threat_scores").select("*").eq("corridor_name", test_corridor).execute()
    
    assert len(select_result.data) > 0, "Threat score write succeeded but entry was not found in table."
    assert select_result.data[0]["threat_level"] == "CRITICAL"
    
    # 3. Clean up the database record
    delete_result = supabase_client.table("cached_threat_scores").delete().eq("corridor_name", test_corridor).execute()
    assert len(delete_result.data) > 0 or delete_result.data is not None
