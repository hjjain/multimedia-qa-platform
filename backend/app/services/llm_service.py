"""LLM service for summarization and question answering."""

from openai import OpenAI
from typing import List, Optional, AsyncGenerator
from app.models.chat import ChatMessage
from app.models.document import TimestampedSegment
from app.config import get_settings


class LLMService:
    """Handles AI-powered summarization and Q&A using OpenAI GPT."""

    def __init__(self):
        self.client = OpenAI(
            api_key=get_settings().openai_api_key
        )
        self.model = "gpt-4-turbo-preview"

    async def generate_summary(self, text: str) -> str:
        """Generate a concise summary of document content.

        Args:
            text: Full document text to summarize.

        Returns:
            Summary string.
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant that summarizes "
                        "documents concisely. Provide a clear, "
                        "structured summary highlighting key points."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Please summarize the following content:"
                        f"\n\n{text[:15000]}"
                    ),
                },
            ],
            max_tokens=500,
        )
        return response.choices[0].message.content

    async def answer_question(
        self,
        question: str,
        context_chunks: List[str],
        timestamps: Optional[List[TimestampedSegment]] = None,
        conversation_history: Optional[List[ChatMessage]] = None,
    ) -> tuple:
        """Answer a question based on retrieved context chunks.

        Args:
            question: User's question.
            context_chunks: Relevant document chunks.
            timestamps: Optional media timestamps.
            conversation_history: Previous conversation messages.

        Returns:
            Tuple of (answer_string, relevant_timestamps_or_None)
        """
        if conversation_history is None:
            conversation_history = []

        context = "\n\n".join(context_chunks)

        system_prompt = (
            "You are a helpful assistant answering questions "
            "based on document content.\n"
            "Answer based ONLY on the provided context. "
            "If the answer isn't in the context, say so.\n"
            "If timestamps are provided and relevant to the "
            "answer, reference them."
        )

        if timestamps:
            timestamp_text = "\n".join(
                [
                    f"[{seg.start_time:.1f}s - {seg.end_time:.1f}s]"
                    f": {seg.text}"
                    for seg in timestamps
                ]
            )
            context += (
                f"\n\nTimestamped Transcript:\n{timestamp_text}"
            )

        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Add last 3 exchanges from conversation history
        for msg in conversation_history[-6:]:
            messages.append(
                {"role": msg.role, "content": msg.content}
            )

        messages.append(
            {
                "role": "user",
                "content": (
                    f"Context:\n{context}\n\nQuestion: {question}"
                ),
            }
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000,
        )

        answer = response.choices[0].message.content

        # Find relevant timestamps if available
        relevant_timestamps = None
        if timestamps:
            relevant_timestamps = (
                self._find_relevant_timestamps(answer, timestamps)
            )

        return answer, relevant_timestamps

    def _find_relevant_timestamps(
        self,
        answer: str,
        timestamps: List[TimestampedSegment],
    ) -> List[dict]:
        """Find timestamps that are relevant to the answer.

        Matches words longer than 4 characters from segment text
        against the answer content.
        """
        relevant = []
        answer_lower = answer.lower()

        for seg in timestamps:
            words = seg.text.lower().split()
            if any(
                word in answer_lower
                for word in words
                if len(word) > 4
            ):
                relevant.append(
                    {
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "text": seg.text,
                    }
                )

        return relevant[:5]  # Limit to top 5

    async def stream_answer(
        self,
        question: str,
        context_chunks: List[str],
        conversation_history: Optional[List[ChatMessage]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream answer tokens for real-time response.

        Yields:
            Individual content tokens as strings.
        """
        if conversation_history is None:
            conversation_history = []

        context = "\n\n".join(context_chunks)

        messages = [
            {
                "role": "system",
                "content": (
                    "Answer based only on the provided context."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Context:\n{context}\n\n"
                    f"Question: {question}"
                ),
            },
        ]

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1000,
            stream=True,
        )

        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
