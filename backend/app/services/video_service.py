"""Video processing service for audio extraction and transcription."""

import ffmpeg
import tempfile
import os
from typing import List, Tuple
from app.models.document import TimestampedSegment
from app.services.audio_service import AudioService


class VideoService:
    """Handles video processing: audio extraction and transcription."""

    def __init__(self):
        self.audio_service = AudioService()

    async def extract_audio(
        self, file_content: bytes, filename: str
    ) -> bytes:
        """Extract audio track from video file using ffmpeg.

        Args:
            file_content: Raw video file bytes.
            filename: Original filename for extension detection.

        Returns:
            Audio content as MP3 bytes.
        """
        suffix = os.path.splitext(filename)[1]

        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False
        ) as video_tmp:
            video_tmp.write(file_content)
            video_path = video_tmp.name

        audio_path = video_path + ".mp3"

        try:
            ffmpeg.input(video_path).output(
                audio_path,
                acodec="libmp3lame",
                ac=1,
                ar="16000",
            ).overwrite_output().run(quiet=True)

            with open(audio_path, "rb") as f:
                audio_content = f.read()

            return audio_content
        finally:
            os.unlink(video_path)
            if os.path.exists(audio_path):
                os.unlink(audio_path)

    async def process_video(
        self,
        file_content: bytes,
        filename: str,
    ) -> Tuple[str, List[TimestampedSegment]]:
        """Extract audio and transcribe with timestamps.

        Returns:
            Tuple of (full_transcript, list_of_timestamped_segments)
        """
        audio_content = await self.extract_audio(
            file_content, filename
        )
        return await self.audio_service.transcribe_with_timestamps(
            audio_content, "audio.mp3"
        )
