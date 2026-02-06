"""Audio transcription service using OpenAI Whisper API."""

import openai
from typing import List, Tuple
from app.models.document import TimestampedSegment
from app.config import get_settings
import tempfile
import os


class AudioService:
    """Handles audio transcription with timestamp extraction."""

    def __init__(self):
        self.client = openai.OpenAI(
            api_key=get_settings().openai_api_key
        )

    async def transcribe_with_timestamps(
        self,
        file_content: bytes,
        filename: str,
    ) -> Tuple[str, List[TimestampedSegment]]:
        """Transcribe audio with segment-level timestamps using Whisper.

        Args:
            file_content: Raw audio file bytes.
            filename: Original filename for extension detection.

        Returns:
            Tuple of (full_transcript, list_of_timestamped_segments)
        """
        suffix = os.path.splitext(filename)[1]
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=open(tmp_path, "rb"),
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

            full_text = response.text
            segments = []

            for segment in response.segments:
                segments.append(
                    TimestampedSegment(
                        start_time=segment["start"],
                        end_time=segment["end"],
                        text=segment["text"],
                    )
                )

            return full_text, segments
        finally:
            os.unlink(tmp_path)

    async def get_timestamps_for_topic(
        self,
        segments: List[TimestampedSegment],
        topic: str,
    ) -> List[TimestampedSegment]:
        """Find segments relevant to a specific topic.

        Uses keyword matching to identify relevant segments.
        """
        topic_lower = topic.lower()
        relevant = []
        for seg in segments:
            if topic_lower in seg.text.lower():
                relevant.append(seg)
        return relevant
