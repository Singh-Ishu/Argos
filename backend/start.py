import os
import sys
import logging
from pathlib import Path

# Configure basic logging for startup script
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("startup")

# Ensure the root workspace directory is in sys.path for backend imports
# If start.py is inside backend/, its grandparent is the workspace root
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Import database and configuration verification
try:
    from backend.app.config import settings
    from backend.app.database import verify_database_tables
except ImportError as e:
    logger.critical(f"Failed to import backend modules: {e}")
    logger.critical("Make sure you run the script from the root workspace directory, or that sys.path is correct.")
    sys.exit(1)


def perform_preflight_db_check():
    """
    Checks Supabase connectivity and reports if the required tables exist.
    """
    logger.info("==================================================")
    logger.info("       ARGOS BACKEND PRE-FLIGHT DATABASE CHECK     ")
    logger.info("==================================================")
    
    # 1. Check environment configuration
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        logger.warning("Supabase credentials not configured in backend/.env!")
        logger.warning("The server will start, but database logging and caching features will degrade gracefully.")
        return False
        
    if "placeholder" in settings.SUPABASE_URL or "placeholder" in settings.SUPABASE_KEY:
        logger.warning("Supabase credentials in backend/.env are placeholders!")
        logger.warning("The server will start, but database logging and caching features will degrade gracefully.")
        return False

    logger.info(f"Connecting to Supabase instance: {settings.SUPABASE_URL}")
    
    # 2. Verify table presence
    db_status = verify_database_tables()
    
    if not db_status["client_connected"]:
        logger.error(f"Failed to connect to Supabase: {db_status['error']}")
        logger.warning("Please verify your internet connection and Supabase credentials.")
        return False
        
    logs_exists = db_status["scenario_execution_logs_exists"]
    threats_exists = db_status["cached_threat_scores_exists"]
    
    if logs_exists and threats_exists:
        logger.info("SUCCESS: All required database tables ('scenario_execution_logs', 'cached_threat_scores') exist.")
        logger.info("==================================================")
        return True
    else:
        logger.warning("--------------------------------------------------")
        logger.warning("WARNING: Required database tables are missing!")
        if not logs_exists:
            logger.warning(" - Table 'scenario_execution_logs' is missing.")
        if not threats_exists:
            logger.warning(" - Table 'cached_threat_scores' is missing.")
        logger.warning("--------------------------------------------------")
        logger.warning("Please initialize your Supabase database using the SQL script:")
        logger.warning(" -> backend/schema.sql")
        logger.warning("--------------------------------------------------")
        logger.warning("Proceeding to launch server in degraded local-only mode...")
        logger.warning("==================================================")
        return False


if __name__ == "__main__":
    # Run preflight db checks
    perform_preflight_db_check()
    
    # Import uvicorn to start the server
    import uvicorn
    
    logger.info("Starting Uvicorn server...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
