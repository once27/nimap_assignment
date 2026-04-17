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
        user: any # Using any to avoid circular import with User model here, but it's a User object
    ) -> List[dict]:
        """
        Two-stage search: 
        1. Bi-Encoder retrieval from Qdrant (Fast)
        2. Cross-Encoder reranking (High Precision)
        """
        # Thresholds to ensure quality
        BI_THRESHOLD = 0.3  # Broad retrieval gate
        CROSS_THRESHOLD = -5.0 # Precision reranking gate 

        try:
            # 1. Generate query embedding
            query_vector = embedding_service.generate_embeddings([query])[0]

            # 2. Build security filters
            # Check if user is Client
            is_client = any(role.name == "Client" for role in user.roles)
            
            if is_client and user.company_name:
                # Client searches across the whole company
                condition = models.FieldCondition(
                    key="company_name",
                    match=models.MatchValue(value=user.company_name)
                )
            else:
                # Others search only their own documents
                condition = models.FieldCondition(
                    key="owner_id",
                    match=models.MatchValue(value=str(user.id))
                )

            must_filters = [condition]

            # 3. Step 1: Broad Retrieval (Spec: Top 20 Candidates)
            search_results = vector_db_service.client.search(
                collection_name=vector_db_service.collection_name,
                query_vector=query_vector,
                query_filter=models.Filter(must=must_filters),
                limit=20 
            )

            # 4. Filter junk and format candidates
            candidates = []
            for res in search_results:
                if res.score < BI_THRESHOLD:
                    continue
                
                candidates.append({
                    "text": res.payload.get("text"),
                    "document_id": UUID(res.payload.get("document_id")),
                    "document_title": res.payload.get("title"),
                    "chunk_index": res.payload.get("chunk_index"),
                    "bi_score": res.score
                })

            if not candidates:
                logger.info(f"No candidates passed Bi-Encoder threshold (0.5) for query: '{query}'")
                return []

            # 5. Step 2: Precision Reranking
            candidate_texts = [c["text"] for c in candidates]
            rerank_scores = embedding_service.rerank(query, candidate_texts)

            # 6. Apply final quality filter and sort
            results = []
            for i, score in enumerate(rerank_scores):
                if score < CROSS_THRESHOLD:
                    continue  # Reranker says this is not relevant

                candidates[i]["score"] = score
                results.append(candidates[i])

            # Sort by final score (High to Low)
            results.sort(key=lambda x: x["score"], reverse=True)
            
            # Return Top 5
            final_results = results[:5]
            logger.info(f"Search complete for '{query}'. Found {len(final_results)} relevant matches.")
            return final_results

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise Exception(f"Search operation failed: {str(e)}")

# Singleton instance
search_service = SearchService()
