/**
 * Memory Search Filter - Apple Design Language
 */

'use client';

import React, { useState } from 'react';
import { Search, X } from 'lucide-react';

interface MemorySearchFilterProps {
  allTags: string[];
  allFileTypes: Record<string, number>;
  onSearch: (query: string, tags: string[], fileType: string | null) => void;
  isLoading: boolean;
}

export default function MemorySearchFilter({ allTags, allFileTypes, onSearch, isLoading }: MemorySearchFilterProps) {
  const [query, setQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedFileType, setSelectedFileType] = useState<string | null>(null);
  const [showTagFilter, setShowTagFilter] = useState(false);
  const [showTypeFilter, setShowTypeFilter] = useState(false);

  const handleSearch = (newQuery: string, newTags: string[], newFileType: string | null) => {
    setQuery(newQuery); setSelectedTags(newTags); setSelectedFileType(newFileType); onSearch(newQuery, newTags, newFileType);
  };

  const handleTagToggle = (tag: string) => {
    const newTags = selectedTags.includes(tag) ? selectedTags.filter((t) => t !== tag) : [...selectedTags, tag];
    handleSearch(query, newTags, selectedFileType);
  };

  const handleFileTypeSelect = (fileType: string | null) => {
    const newFileType = selectedFileType === fileType ? null : fileType;
    handleSearch(query, selectedTags, newFileType); setShowTypeFilter(false);
  };

  const hasActiveFilters = query || selectedTags.length > 0 || selectedFileType;

  return (
    <div className="apple-utility-card">
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-apple-ink-48" />
          <input type="text" name="memory-search" aria-label="Search memories" value={query} onChange={(e) => handleSearch(e.target.value, selectedTags, selectedFileType)} placeholder="Search title, description…" disabled={isLoading} className="apple-search-input pl-10" />
          {query && (
            <button onClick={() => handleSearch('', selectedTags, selectedFileType)} className="absolute right-3 top-1/2 -translate-y-1/2 text-apple-ink-48 hover:text-apple-ink" aria-label="Clear search">
              <X className="h-5 w-5" />
            </button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        <div className="relative">
          <button onClick={() => setShowTypeFilter(!showTypeFilter)} className={`px-3 py-2 rounded-apple-pill text-apple-caption font-medium transition-colors ${selectedFileType ? 'bg-apple-blue/10 text-apple-blue border border-apple-blue/30' : 'bg-apple-parchment text-apple-ink border border-apple-hairline hover:bg-apple-chip/20'}`} aria-label={`File type filter${selectedFileType ? `, ${selectedFileType} selected` : ''}`} aria-expanded={showTypeFilter}>
            {selectedFileType ? `Type: ${selectedFileType}` : 'File Type'}
          </button>
          {showTypeFilter && (
            <div className="absolute top-full mt-2 left-0 bg-apple-canvas border border-apple-hairline rounded-apple-sm shadow-lg z-10 min-w-48">
              <div className="p-2">
                {Object.entries(allFileTypes).map(([fileType, count]) => (
                  <button key={fileType} onClick={() => handleFileTypeSelect(fileType)} className={`w-full text-left px-3 py-2 rounded-apple-sm text-apple-caption transition-colors ${selectedFileType === fileType ? 'bg-apple-blue/10 text-apple-blue' : 'hover:bg-apple-parchment text-apple-ink'}`}>
                    {fileType} ({count})
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {allTags.length > 0 && (
          <div className="relative">
            <button onClick={() => setShowTagFilter(!showTagFilter)} className={`px-3 py-2 rounded-apple-pill text-apple-caption font-medium transition-colors ${selectedTags.length > 0 ? 'bg-apple-blue/10 text-apple-blue border border-apple-blue/30' : 'bg-apple-parchment text-apple-ink border border-apple-hairline hover:bg-apple-chip/20'}`} aria-label={`Tags filter${selectedTags.length > 0 ? `, ${selectedTags.length} selected` : ''}`} aria-expanded={showTagFilter}>
              Tags {selectedTags.length > 0 && `(${selectedTags.length})`}
            </button>
            {showTagFilter && (
              <div className="absolute top-full mt-2 left-0 bg-apple-canvas border border-apple-hairline rounded-apple-sm shadow-lg z-10 min-w-56 max-h-64 overflow-y-auto">
                <div className="p-2">
                  {allTags.map((tag) => (
                    <label key={tag} className="flex items-center px-3 py-2 rounded-apple-sm hover:bg-apple-parchment cursor-pointer text-apple-caption">
                      <input type="checkbox" checked={selectedTags.includes(tag)} onChange={() => handleTagToggle(tag)} className="w-4 h-4 rounded border-apple-hairline text-apple-blue" />
                      <span className="ml-2">{tag}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {hasActiveFilters && (
          <button onClick={() => handleSearch('', [], null)} className="apple-btn-secondary text-apple-caption">
            Clear Filters
          </button>
        )}
      </div>

      {hasActiveFilters && (
        <div className="mt-3 pt-3 border-t border-apple-hairline">
          <div className="text-apple-fine-print text-apple-ink-48">
            {query && <span>Searching: <span className="text-apple-ink">{query}</span></span>}
            {selectedTags.length > 0 && <span className="ml-3">Tags: <span className="text-apple-ink">{selectedTags.join(', ')}</span></span>}
            {selectedFileType && <span className="ml-3">Type: <span className="text-apple-ink">{selectedFileType}</span></span>}
          </div>
        </div>
      )}
    </div>
  );
}
