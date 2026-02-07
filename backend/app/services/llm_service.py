"""LLM service using Replicate (GPT-5.2) for summarization and Q&A."""

import os
import replicate
from typing import List, Optional, AsyncGenerator
from app.models.chat import ChatMessage
from app.models.document import TimestampedSegment
from app.config import get_settings


class LLMService:
    """Handles summarization and Q&A using Replicate GPT-5.2."""

    def __init__(self):
        settings = get_settings()
        os.environ["REPLICATE_API_TOKEN"] = (
            settings.replicate_api_token
        )
        self.model = settings.llm_model

    async def generate_summary(self, text: str) -> str:
        """Generate summary of document content."""
        output = replicate.run(
            self.model,
            input={
                "prompt": (
                    "Please summarize the following content "
                    "concisely, highlighting key points:\n\n"
                    f"{text[:10000]}"
                ),
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that "
                            "summarizes documents. Provide a "
                            "clear, structured summary."
                        ),
                    }
                ],
                "reasoning_effort": "low",
            },
        )
        return "".join(output)

    async def answer_question(
        self,
        question: str,
        context_chunks: List[str],
        timestamps: Optional[List[TimestampedSegment]] = None,
        conversation_history: Optional[List[ChatMessage]] = None,
    ) -> tuple:
        """Answer question based on retrieved context."""
        if conversation_history is None:
            conversation_history = []

        context = "\n\n".join(context_chunks)

        system_msg = (
            "You are a helpful assistant answering questions "
            "based on document content. "
            "Answer based ONLY on the provided context. "
            "If the answer isn't in the context, say so. "
            "If timestamps are provided, reference them."
        )

        if timestamps:
            ts_text = "\n".join(
                [
                    f"[{s.start_time:.1f}s - {s.end_time:.1f}s]"
                    f": {s.text}"
                    for s in timestamps
                ]
            )
            context += f"\n\nTimestamped Transcript:\n{ts_text}"

        # Build messages with conversation history
        messages = [{"role": "system", "content": system_msg}]
        for msg in conversation_history[-6:]:
            messages.append(
                {"role": msg.role, "content": msg.content}
            )

        prompt = f"Context:\n{context}\n\nQuestion: {question}"

        output = replicate.run(
            self.model,
            input={
                "prompt": prompt,
                "messages": messages,
                "reasoning_effort": "medium",
            },
        )
        answer = "".join(output)

        relevant_timestamps = None
        if timestamps:
            relevant_timestamps = (
                self._find_relevant_timestamps(
                    answer, timestamps
                )
            )
        return answer, relevant_timestamps

    def _find_relevant_timestamps(
        self,
        answer: str,
        timestamps: List[TimestampedSegment],
    ) -> List[dict]:
        """Find timestamps mentioned or relevant to answer."""
        relevant = []
        answer_lower = answer.lower()

        for seg in timestamps:
            if any(
                word in answer_lower
                for word in seg.text.lower().split()
                if len(word) > 4
            ):
                relevant.append(
                    {
                        "start_time": seg.start_time,
                        "end_time": seg.end_time,
                        "text": seg.text,
                    }
                )
        return relevant[:5]

    async def stream_answer(
        self,
        question: str,
        context_chunks: List[str],
        conversation_history: Optional[List[ChatMessage]] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream answer tokens for real-time response."""
        if conversation_history is None:
            conversation_history = []

        context = "\n\n".join(context_chunks)

        messages = [
            {
                "role": "system",
                "content": "Answer based only on the context.",
            }
        ]
        for msg in conversation_history[-6:]:
            messages.append(
                {"role": msg.role, "content": msg.content}
            )

        output = replicate.run(
            self.model,
            input={
                "prompt": (
                    f"Context:\n{context}\n\n"
                    f"Question: {question}"
                ),
                "messages": messages,
                "reasoning_effort": "medium",
            },
        )
        for token in output:
            yield token
