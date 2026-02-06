import React, { useRef, useImperativeHandle, forwardRef } from 'react';
import { Play } from 'lucide-react';
import { getMediaUrl } from '../services/api';

/**
 * Media player component that supports audio and video playback.
 * Exposes a seekTo method via ref for timestamp navigation.
 */
const MediaPlayer = forwardRef(({ documentId, fileType, filename }, ref) => {
  const mediaRef = useRef(null);

  useImperativeHandle(ref, () => ({
    seekTo: (time) => {
      if (mediaRef.current) {
        mediaRef.current.currentTime = time;
        mediaRef.current.play();
      }
    },
  }));

  const mediaUrl = getMediaUrl(documentId);
  const isVideo = fileType === 'video';

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="p-4 border-b flex items-center gap-2">
        <Play className="w-5 h-5 text-blue-500" />
        <h2 className="font-semibold text-gray-800">Media Player</h2>
      </div>

      <div className="bg-black">
        {isVideo ? (
          <video
            ref={mediaRef}
            src={mediaUrl}
            controls
            className="w-full max-h-[400px]"
          >
            Your browser does not support video playback.
          </video>
        ) : (
          <div className="p-4">
            <audio ref={mediaRef} src={mediaUrl} controls className="w-full">
              Your browser does not support audio playback.
            </audio>
          </div>
        )}
      </div>

      <div className="p-3 bg-gray-50 text-sm text-gray-600 flex items-center justify-between">
        <span className="truncate">{filename}</span>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
          {fileType}
        </span>
      </div>
    </div>
  );
});

MediaPlayer.displayName = 'MediaPlayer';

export default MediaPlayer;
