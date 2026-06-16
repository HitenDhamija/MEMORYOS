'use client';

import React, { useState, useEffect } from 'react';
import { Search, X } from 'lucide-react';

interface MemorySearchFilterProps {
  allTags: string[];
  allFileTypes: Record<string, number>;
  onSearch: (query: string, tags: string[], fileType: string | null) => void;
  isLoading: boolean;
}

export default function MemorySearchFilter({
  allTags,
  allFileTypes,
  onSearch,
  isLoading,
}: MemorySearchFilterProps) {
  const [query, setQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedFileType, setSelectedFileType] = useState<string | null>(null);
  const [showTagFilter, setShowTagFilter] = useState(false);
  const [showTypeFilter, setShowTypeFilter] = useState(false);

  const handleSearch = (newQuery: string, newTags: string[], newFileType: string | null) => {
    setQuery(newQuery);
    setSelectedTags(newTags);
    setSelectedFileType(newFileType);
    onSearch(newQuery, newTags, newFileType);
  };

  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value;
    handleSearch(newQuery, selectedTags, selectedFileType);
  };

  const handleTagToggle = (tag: string) => {
    const newTags = selectedTags.includes(tag)
      ? selectedTags.filter((t) => t !== tag)
      : [...selectedTags, tag];
    handleSearch(query, newTags, selectedFileType);
  };

  const handleFileTypeSelect = (fileType: string | null) => {
    const newFileType = selectedFileType === fileType ? null : fileType;
    handleSearch(query, selectedTags, newFileType);
    setShowTypeFilter(false);
  };

  const handleClearFilters = () => {
    handleSearch('', [], null);
    setShowTagFilter(false);
    setShowTypeFilter(false);
  };

  const hasActiveFilters = query || selectedTags.length > 0 || selectedFileType;

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm">
      {/* Search Input */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            value={query}
            onChange={handleQueryChange}
            placeholder="Search title, description..."
            disabled={isLoading}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          />
          {query && (
            <button
              onClick={() => handleSearch('', selectedTags, selectedFileType)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>

      {/* Filter Buttons */}
      <div className="flex flex-wrap gap-2">
        {/* File Type Filter */}
        <div className="relative">
          <button
            onClick={() => setShowTypeFilter(!showTypeFilter)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              selectedFileType
                ? 'bg-blue-100 text-blue-700 border border-blue-300'
                : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
            }`}
          >
            {selectedFileType ? `Type: ${selectedFileType}` : 'File Type'}
          </button>

          {showTypeFilter && (
            <div className="absolute top-full mt-2 left-0 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-48">
              <div className="p-2">
                {Object.entries(allFileTypes).map(([fileType, count]) => (
                  <button
                    key={fileType}
                    onClick={() => handleFileTypeSelect(fileType)}
                    className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                      selectedFileType === fileType
                        ? 'bg-blue-100 text-blue-700'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    {fileType} ({count})
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Tags Filter */}
        {allTags.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setShowTagFilter(!showTagFilter)}
              className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedTags.length > 0
                  ? 'bg-blue-100 text-blue-700 border border-blue-300'
                  : 'bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200'
              }`}
            >
              Tags {selectedTags.length > 0 && `(${selectedTags.length})`}
            </button>

            {showTagFilter && (
              <div className="absolute top-full mt-2 left-0 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-56 max-h-64 overflow-y-auto">
                <div className="p-2">
                  {allTags.length > 0 ? (
                    allTags.map((tag) => (
                      <label
                        key={tag}
                        className="flex items-center px-3 py-2 rounded hover:bg-gray-100 cursor-pointer text-sm"
                      >
                        <input
                          type="checkbox"
                          checked={selectedTags.includes(tag)}
                          onChange={() => handleTagToggle(tag)}
                          className="w-4 h-4 rounded border-gray-300"
                        />
                        <span className="ml-2">{tag}</span>
                      </label>
                    ))
                  ) : (
                    <p className="px-3 py-2 text-gray-500 text-sm">
                      No tags available
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Clear Filters Button */}
        {hasActiveFilters && (
          <button
            onClick={handleClearFilters}
            className="px-3 py-2 rounded-lg text-sm font-medium bg-gray-100 text-gray-700 border border-gray-300 hover:bg-gray-200 transition-colors"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-600">
            {query && (
              <span>
                Searching: <span className="font-medium">{query}</span>
              </span>
            )}
            {selectedTags.length > 0 && (
              <span className="ml-3">
                Tags: <span className="font-medium">{selectedTags.join(', ')}</span>
              </span>
            )}
            {selectedFileType && (
              <span className="ml-3">
                Type: <span className="font-medium">{selectedFileType}</span>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
