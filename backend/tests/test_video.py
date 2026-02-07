"""Tests for video processing service."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.models.document import TimestampedSegment


class TestVideoService:
    """Tests for video audio extraction and transcription."""

    @pytest.mark.asyncio
    async def test_extract_audio(self):
        """Test ffmpeg audio extraction from video."""
        with patch(
            "app.services.video_service.ffmpeg"
        ) as mock_ff:
            mock_input = MagicMock()
            mock_output = MagicMock()
            mock_overwrite = MagicMock()
            mock_ff.input.return_value = mock_input
            mock_input.output.return_value = mock_output
            mock_output.overwrite_output.return_value = (
                mock_overwrite
            )
            mock_overwrite.run = MagicMock()

            with patch(
                "builtins.open",
                MagicMock(
                    return_value=MagicMock(
                        read=MagicMock(
                            return_value=b"audio-data"
                        ),
                        __enter__=MagicMock(
                            return_value=MagicMock(
                                read=MagicMock(
                                    return_value=b"audio-data"
                                )
                            )
                        ),
                        __exit__=MagicMock(
                            return_value=False
                        ),
                    )
                ),
            ), patch(
                "os.path.exists", return_value=True
            ), patch(
                "os.unlink"
            ):
                from app.services.video_service import (
                    VideoService,
                )

                service = VideoService()
                audio = await service.extract_audio(
                    b"video-bytes", "test.mp4"
                )
                assert audio == b"audio-data"

    @pytest.mark.asyncio
    async def test_process_video(self):
        """Test full video processing pipeline."""
        from app.services.video_service import VideoService

        service = VideoService()

        service.extract_audio = AsyncMock(
            return_value=b"audio-bytes"
        )
        service.audio_service.transcribe_with_timestamps = (
            AsyncMock(
                return_value=(
                    "Video transcript",
                    [
                        TimestampedSegment(
                            start_time=0.0,
                            end_time=5.0,
                            text="Video segment",
                        )
                    ],
                )
            )
        )

        text, segments = await service.process_video(
            b"video-bytes", "test.mp4"
        )
        assert text == "Video transcript"
        assert len(segments) == 1
        assert segments[0].text == "Video segment"

    @pytest.mark.asyncio
    async def test_process_video_calls_extract(self):
        """Test that process_video calls extract_audio first."""
        from app.services.video_service import VideoService

        service = VideoService()
        service.extract_audio = AsyncMock(
            return_value=b"extracted-audio"
        )
        service.audio_service.transcribe_with_timestamps = (
            AsyncMock(
                return_value=(
                    "text",
                    [
                        TimestampedSegment(
                            start_time=0.0,
                            end_time=1.0,
                            text="seg",
                        )
                    ],
                )
            )
        )

        await service.process_video(
            b"video-data", "clip.mp4"
        )
        service.extract_audio.assert_called_once_with(
            b"video-data", "clip.mp4"
        )
        service.audio_service.transcribe_with_timestamps.assert_called_once_with(
            b"extracted-audio", "audio.mp3"
        )
