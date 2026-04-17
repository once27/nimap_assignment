from sentence_transformers import SentenceTransformer
from typing import List
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        logger.info(f"Initializing embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Convert a list of text chunks into a list of vector embeddings.
        """
        try:
            logger.info(f"Generating embeddings for {len(texts)} chunks")
            embeddings = self.model.encode(texts)
            # Convert numpy array to list of floats
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")

# Singleton instance
embedding_service = EmbeddingService()
