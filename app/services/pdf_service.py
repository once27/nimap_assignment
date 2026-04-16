import pdfplumber
import os
from typing import List
from app.core.logger import setup_logger

logger = setup_logger(__name__)

class PDFService:
    @staticmethod
    def extract_text(file_path: str) -> str:
        """
        Extract text from a document (PDF or TXT).
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            raise FileNotFoundError(f"File not found at {file_path}")

        file_extension = os.path.splitext(file_path)[1].lower()

        try:
            # Handle Plain Text files
            if file_extension == ".txt":
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()

            # Handle PDF files
            elif file_extension == ".pdf":
                full_text = []
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text = page.extract_text()
                        if text:
                            full_text.append(text)
                return "\n\n".join(full_text)

            else:
                logger.warning(f"Unsupported file format: {file_extension}")
                raise ValueError(f"Unsupported file format: {file_extension}")

        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            raise Exception(f"Failed to extract text: {str(e)}")

pdf_service = PDFService()
