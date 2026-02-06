import React, { useState } from 'react';
import { Clock, Search, Play } from 'lucide-react';
import { searchTimestamps } from '../services/api';

/**
 * Timestamp list component with search capability.
 * Displays clickable timestamps that seek the media player.
 */
export default function TimestampList({
  documentId,
  timestamps,
  onTimestampClick,
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredTimestamps, setFilteredTimestamps] = useState(null);
  const [isSearching, setIsSearching] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setFilteredTimestamps(null);
      return;
    }

    setIsSearching(true);
    try {
      const result = await searchTimestamps(documentId, searchQuery);
      setFilteredTimestamps(result.timestamps);
    } catch (error) {
      console.error('Timestamp search failed:', error);
    } finally {
      setIsSearching(false);
    }
  };

  const clearSearch = () => {
    setFilteredTimestamps(null);
    setSearchQuery('');
  };

  const displayTimestamps = filteredTimestamps || timestamps;

  return (
    <div className="bg-white rounded-xl shadow-lg p-6">
      <div className="flex items-center gap-3 mb-4">
        <Clock className="w-6 h-6 text-purple-500" />
        <h2 className="font-semibold text-gray-800">Timestamps</h2>
        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
          {displayTimestamps.length} segments
        </span>
      </div>

      {/* Search Bar */}
      <form onSubmit={handleSearch} className="mb-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search timestamps by topic..."
            className="flex-1 p-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
          />
          <button
            type="submit"
            disabled={isSearching}
            className="p-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 disabled:opacity-50 transition-colors"
          >
            <Search className="w-4 h-4" />
          </button>
        </div>
      </form>

      {/* Timestamp List */}
      <div className="max-h-[300px] overflow-y-auto space-y-2">
        {displayTimestamps.length === 0 ? (
          <p className="text-gray-500 text-sm text-center py-4">
            No timestamps found
          </p>
        ) : (
          displayTimestamps.map((ts, idx) => (
            <button
              key={idx}
              onClick={() => onTimestampClick(ts.start_time)}
              className="w-full text-left p-3 rounded-lg bg-gray-50 hover:bg-purple-50 transition-colors group flex items-start gap-3"
            >
              <span className="shrink-0 text-xs font-mono bg-purple-100 text-purple-700 px-2 py-1 rounded mt-0.5">
                {formatTime(ts.start_time)}
              </span>
              <span className="text-sm text-gray-700 line-clamp-2 flex-1">
                {ts.text}
              </span>
              <Play className="w-4 h-4 text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 mt-0.5" />
            </button>
          ))
        )}
      </div>

      {filteredTimestamps && (
        <button
          onClick={clearSearch}
          className="mt-3 text-sm text-purple-600 hover:underline"
        >
          Clear search - show all timestamps
        </button>
      )}
    </div>
  );
}

function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
