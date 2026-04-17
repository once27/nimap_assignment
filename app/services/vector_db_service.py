from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any
import uuid
from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class VectorDBService:
    def __init__(self):
        self.host = settings.QDRANT_HOST
        self.port = settings.QDRANT_PORT
        self.collection_name = "financial_docs"
        
        logger.info(f"Connecting to Qdrant at {self.host}:{self.port}")
        self.client = QdrantClient(host=self.host, port=self.port)
        self._ensure_collection()

    def _ensure_collection(self):
        """
        Create the collection if it doesn't already exist.
        """
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                logger.info(f"Creating Qdrant collection: {self.collection_name}")
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=384,  # Size for all-MiniLM-L6-v2
                        distance=models.Distance.COSINE
                    )
                )
        except Exception as e:
            logger.error(f"Error ensuring Qdrant collection exists: {e}")

    def upsert_chunks(self, document_id: str, chunks: List[str], embeddings: List[List[float]], metadata: Dict[str, Any]):
        """
        Store chunks and their embeddings into Qdrant.
        """
        points = []
        for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):
            point_id = str(uuid.uuid4())
            points.append(models.PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "document_id": document_id,
                    "chunk_index": i,
                    "text": chunk,
                    **metadata
                }
            ))

        try:
            logger.info(f"Upserting {len(points)} points to Qdrant for document {document_id}")
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert points to Qdrant: {e}")
            return False
    def delete_document_embeddings(self, document_id: str):
        """
        Remove all vectors associated with a specific document ID.
        """
        try:
            logger.info(f"Removing points for document {document_id} from Qdrant")
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchValue(value=document_id)
                            )
                        ]
                    )
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete points from Qdrant: {e}")
            return False
    def get_document_chunks(self, document_id: str, owner_id: str):
        """
        Retrieve all chunks and metadata for a specific document, restricted by owner.
        """
        try:
            # We use scroll to get all points instead of search (no vector needed)
            scroll_results, _ = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="document_id",
                            match=models.MatchValue(value=document_id)
                        ),
                        models.FieldCondition(
                            key="owner_id",
                            match=models.MatchValue(value=owner_id)
                        )
                    ]
                ),
                limit=100,  # A document shouldn't have more than 100 chunks usually
                with_payload=True,
                with_vectors=False
            )
            
            # Sort by chunk_index to preserve document order
            chunks = []
            for point in scroll_results:
                chunks.append({
                    "text": point.payload.get("text"),
                    "chunk_index": point.payload.get("chunk_index"),
                    "metadata": {
                        "title": point.payload.get("title"),
                        "document_type": point.payload.get("document_type"),
                        "company_name": point.payload.get("company_name")
                    }
                })
            
            chunks.sort(key=lambda x: x["chunk_index"])
            return chunks
        except Exception as e:
            logger.error(f"Failed to retrieve document chunks from Qdrant: {e}")
            return []

    def cleanup_orphaned_embeddings(self, valid_document_ids: List[str], owner_id: str):
        """
        Remove all vectors for this user that don't belong to the provided list of valid IDs.
        """
        try:
            logger.info(f"Checking for orphaned embeddings in Qdrant for owner {owner_id}")
            # We want to delete points where:
            # 1. owner_id == current_user.id
            # 2. document_id NOT IN valid_document_ids
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=models.Filter(
                        must=[
                            models.FieldCondition(
                                key="owner_id",
                                match=models.MatchValue(value=owner_id)
                            )
                        ],
                        must_not=[
                            models.FieldCondition(
                                key="document_id",
                                match=models.MatchAny(any=valid_document_ids)
                            )
                        ]
                    )
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to cleanup orphaned embeddings: {e}")
            return False

# Singleton instance
vector_db_service = VectorDBService()
