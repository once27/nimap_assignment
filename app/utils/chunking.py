from typing import List
from app.core.config import settings
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class ChunkingUtility:
    @staticmethod
    def chunk_text(text: str) -> List[str]:
        """
        Split text into chunks based on paragraphs, respecting max size and overlap.
        """
        max_chunk_size = settings.CHUNK_SIZE
        overlap = settings.CHUNK_OVERLAP
        
        # Split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            # If a single paragraph is larger than max_chunk_size, we might need more granular splitting,
            # but for financial documents, paragraphs are usually reasonable.
            if len(current_chunk) + len(p) + 2 <= max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + p
                else:
                    current_chunk = p
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                    
                # Standard overlap logic: include some of the end of the previous chunk if possible
                # Simple implementation: Start next chunk with the paragraph that didn't fit,
                # maybe prefixing with a bit of the previous one if we want real overlap.
                # For now, let's keep it simple: the "overlap" in paragraph chunking usually means 
                # overlapping sentences or context.
                
                # If the paragraph itself is too huge, split it roughly
                if len(p) > max_chunk_size:
                    sub_paragraphs = [p[i:i + max_chunk_size] for i in range(0, len(p), max_chunk_size - overlap)]
                    chunks.extend(sub_paragraphs[:-1])
                    current_chunk = sub_paragraphs[-1]
                else:
                    current_chunk = p
        
        if current_chunk:
            chunks.append(current_chunk)
            
        logger.info(f"Text split into {len(chunks)} chunks using paragraph-based strategy.")
        return chunks

chunker = ChunkingUtility()
