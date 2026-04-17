import sys
import os

# Add app directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_db_service import vector_db_service
from app.core.logger import setup_logger

logger = setup_logger(__name__)

def reset_collection():
    try:
        logger.info(f"Attempting to delete collection: {vector_db_service.collection_name}")
        success = vector_db_service.client.delete_collection(vector_db_service.collection_name)
        if success:
            logger.info("Successfully deleted collection. It will be re-created with correct settings on next index operation.")
        else:
            logger.error("Failed to delete collection.")
    except Exception as e:
        logger.error(f"Error during collection reset: {e}")

if __name__ == "__main__":
    reset_collection()
