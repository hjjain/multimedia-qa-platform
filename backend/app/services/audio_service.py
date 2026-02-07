"""Audio transcription service using Replicate Whisper."""

import os
import replicate
from typing import List, Tuple
from app.models.document import TimestampedSegment
from app.config import get_settings
import tempfile


class AudioService:
    """Handles audio transcription with timestamp extraction
    using Whisper via Replicate."""

    def __init__(self):
        settings = get_settings()
        os.environ["REPLICATE_API_TOKEN"] = (
            settings.replicate_api_token
        )
        self.whisper_model = settings.whisper_model

    async def transcribe_with_timestamps(
        self,
        file_content: bytes,
        filename: str,
    ) -> Tuple[str, List[TimestampedSegment]]:
        """Transcribe audio with timestamps using Whisper."""
        suffix = os.path.splitext(filename)[1] or ".mp3"
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            output = replicate.run(
                self.whisper_model,
                input={
                    "audio": open(tmp_path, "rb"),
                    "model": "large-v3",
                    "transcription": "plain text",
                },
            )

            # Parse Replicate Whisper output
            if isinstance(output, dict):
                full_text = output.get(
                    "transcription", ""
                )
                raw_segments = output.get("segments", [])
            else:
                full_text = str(output)
                raw_segments = []

            segments = []
            for seg in raw_segments:
                segments.append(
                    TimestampedSegment(
                        start_time=float(
                            seg.get("start", 0)
                        ),
                        end_time=float(seg.get("end", 0)),
                        text=seg.get("text", "").strip(),
                    )
                )

            if not segments and full_text:
                segments.append(
                    TimestampedSegment(
                        start_time=0.0,
                        end_time=0.0,
                        text=full_text[:500],
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
        """Find segments relevant to a specific topic."""
        topic_lower = topic.lower()
        return [
            seg
            for seg in segments
            if topic_lower in seg.text.lower()
        ]
