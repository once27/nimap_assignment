from typing import List, Optional
from uuid import UUID
from qdrant_client.http import models

from app.services.vector_db_service import vector_db_service
from app.services.embedding_service import embedding_service
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class SearchService:
    def search(
        self, 
        query: str, 
        owner_id: UUID
    ) -> List[dict]:
        """
        Search for the most relevant text chunks across all documents owned by the user.
        """
        # Minimum score threshold to filter out irrelevant matches (0.0 to 1.0 for Cosine)
        MIN_SCORE_THRESHOLD = 0.6 

        try:
            # 1. Generate embedding for the query
            query_vector = embedding_service.generate_embeddings([query])[0]

            # 2. Build filters
            must_filters = [
                models.FieldCondition(
                    key="owner_id",
                    match=models.MatchValue(value=str(owner_id))
                )
            ]

            # 3. Perform search in Qdrant
            logger.info(f"--- SEMANTIC SEARCH DEBUG ---")
            logger.info(f"Query: '{query}' | Target Owner: {owner_id}")
            
            search_results = vector_db_service.client.search(
                collection_name=vector_db_service.collection_name,
                query_vector=query_vector,
                query_filter=models.Filter(must=must_filters),
                limit=5
            )

            logger.info(f"Raw Search Results from Qdrant: {len(search_results)}")
            
            # 4. Format and Filter results
            results = []
            for res in search_results:
                if res.score < MIN_SCORE_THRESHOLD:
                    logger.info(f"Skipping result with low score: {res.score} (Threshold: {MIN_SCORE_THRESHOLD})")
                    continue

                logger.info(f"Match accepted: doc_id={res.payload.get('document_id')} | score={res.score}")
                results.append({
                    "text": res.payload.get("text"),
                    "document_id": UUID(res.payload.get("document_id")),
                    "document_title": res.payload.get("title"),
                    "chunk_index": res.payload.get("chunk_index"),
                    "score": res.score
                })

            logger.info(f"Final Filtered Results Count: {len(results)}")
            return results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise Exception(f"Search operation failed: {str(e)}")

# Singleton instance
search_service = SearchService()
