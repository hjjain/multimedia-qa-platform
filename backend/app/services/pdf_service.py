"""PDF processing service for text extraction and chunking."""

from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Tuple
import io


class PDFService:
    """Handles PDF text extraction and chunking for embeddings."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )

    async def extract_text(self, file_content: bytes) -> str:
        """Extract text from PDF bytes."""
        pdf = PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text() or ""
        return text

    async def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks for embedding."""
        return self.text_splitter.split_text(text)

    async def process_pdf(
        self, file_content: bytes
    ) -> Tuple[str, List[str]]:
        """Extract and chunk PDF content.

        Returns:
            Tuple of (full_text, list_of_chunks)
        """
        text = await self.extract_text(file_content)
        chunks = await self.chunk_text(text)
        return text, chunks
