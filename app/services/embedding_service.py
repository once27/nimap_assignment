from sentence_transformers import SentenceTransformer, CrossEncoder
from typing import List, Tuple
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class EmbeddingService:
    def __init__(
        self, 
        model_name: str = "all-MiniLM-L6-v2",
        reranker_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    ):
        logger.info(f"Initializing embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        logger.info(f"Initializing reranker model: {reranker_name}")
        self.reranker = CrossEncoder(reranker_name)

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

    def rerank(self, query: str, documents: List[str]) -> List[float]:
        """
        Score a list of documents against a query using a Cross-Encoder.
        Returns a list of relevance scores.
        """
        try:
            logger.info(f"Reranking {len(documents)} results for query: '{query}'")
            # Pair query with each document
            pairs = [[query, doc] for doc in documents]
            scores = self.reranker.predict(pairs)
            return scores.tolist()
        except Exception as e:
            logger.error(f"Error during reranking: {e}")
            return [0.0] * len(documents)

# Singleton instance
embedding_service = EmbeddingService()
