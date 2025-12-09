"""Application configuration."""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)

logger = logging.getLogger(__name__)

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Environment variables
ALLOYDB_CONNECTION_STRING = os.environ.get("ALLOYDB_CONNECTION_STRING")
GOOGLE_DRIVE_FOLDER_ID = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")
VERTEX_AI_EMBEDDING_MODEL = os.environ.get("VERTEX_AI_EMBEDDING_MODEL", "text-embedding-005")
GEMINI_MODEL_NAME = os.environ.get("GEMINI_MODEL_NAME", "gemini-2.5-flash")

# Validate required environment variables
required_vars = {
    "ALLOYDB_CONNECTION_STRING": ALLOYDB_CONNECTION_STRING,
    "GOOGLE_DRIVE_FOLDER_ID": GOOGLE_DRIVE_FOLDER_ID,
}

missing_vars = [var for var, value in required_vars.items() if not value]
if missing_vars:
    logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")

