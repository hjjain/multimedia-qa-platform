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
                    "language": "auto",
                    "translate": False,
                    "temperature": 0,
                    "transcription": "plain text",
                    "suppress_tokens": "-1",
                    "no_speech_threshold": 0.6,
                    "condition_on_previous_text": True,
                    "compression_ratio_threshold": 2.4,
                    "temperature_increment_on_fallback": 0.2,
                },
            )

            # Parse Replicate Whisper output
            full_text = ""
            segments = []

            if isinstance(output, dict):
                full_text = output.get(
                    "transcription", ""
                )
                raw_segments = output.get("segments", [])
                for seg in raw_segments:
                    start = float(seg.get("start", 0))
                    end = float(seg.get("end", 0))
                    text = seg.get("text", "").strip()
                    if text:
                        segments.append(
                            TimestampedSegment(
                                start_time=start,
                                end_time=end,
                                text=text,
                            )
                        )
            else:
                full_text = str(output)

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
