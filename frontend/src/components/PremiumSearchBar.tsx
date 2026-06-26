/**
 * Premium Global Search Bar Component
 * 
 * Beautiful search interface with suggestions, recent searches,
 * and quick filters.
 */

'use client';

import React, { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Search, Clock, Zap, FolderOpen, BookOpen, Compass, X } from 'lucide-react';
import { apiClient } from '@/lib/apiClient';

export interface SearchResult {
  id: string;
  type: 'memory' | 'collection' | 'topic';
  title: string;
  description?: string;
  icon: string;
  url: string;
}

interface RecentSearch {
  query: string;
  timestamp: Date;
}

export const PremiumSearchBar: React.FC<{
  placeholder?: string;
  onSearch?: (query: string) => void;
}> = ({ placeholder = 'Search memories, collections...', onSearch }) => {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [recentSearches, setRecentSearches] = useState<RecentSearch[]>([]);
  const [loading, setLoading] = useState(false);
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Load recent searches from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('recentSearches');
    if (stored) {
      try {
        setRecentSearches(JSON.parse(stored).map((s: any) => ({
          ...s,
          timestamp: new Date(s.timestamp),
        })));
      } catch (error) {
        console.error('Failed to load recent searches:', error);
      }
    }
  }, []);

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearch = async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      return;
    }

    try {
      setLoading(true);
      // Call semantic search endpoint
      const response = await apiClient.get(`/search?q=${encodeURIComponent(searchQuery)}&limit=10`);
      
      const transformed: SearchResult[] = response.data.results?.map((item: any) => ({
        id: item.id,
        type: item.type || 'memory',
        title: item.filename || item.name || item.title,
        description: item.content?.substring(0, 100),
        icon: item.type === 'collection' ? '📂' : '📄',
        url: item.type === 'collection' ? `/collections/${item.id}` : `/memories/${item.id}`,
      })) || [];

      setResults(transformed);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setQuery(value);
    setIsOpen(true);

    if (value) {
      handleSearch(value);
    } else {
      setResults([]);
    }
  };

  const handleSelectResult = (result: SearchResult) => {
    // Save to recent searches
    const newRecent: RecentSearch[] = [
      { query: result.title, timestamp: new Date() },
      ...recentSearches.filter((s) => s.query !== result.title).slice(0, 4),
    ];
    setRecentSearches(newRecent);
    localStorage.setItem('recentSearches', JSON.stringify(newRecent));

    // Navigate
    router.push(result.url);
    setQuery('');
    setIsOpen(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      // Save to recent searches
      const newRecent: RecentSearch[] = [
        { query, timestamp: new Date() },
        ...recentSearches.filter((s) => s.query !== query).slice(0, 4),
      ];
      setRecentSearches(newRecent);
      localStorage.setItem('recentSearches', JSON.stringify(newRecent));

      onSearch?.(query);
      router.push(`/search?q=${encodeURIComponent(query)}`);
      setQuery('');
      setIsOpen(false);
    }
  };

  const clearQuery = () => {
    setQuery('');
    setResults([]);
    inputRef.current?.focus();
  };

  return (
    <div ref={searchRef} className="relative w-full max-w-2xl mx-auto">
      {/* Search input */}
      <form onSubmit={handleSubmit}>
        <div className="relative">
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400">
            <Search size={20} />
          </div>

          <input
            ref={inputRef}
            type="text"
            name="search"
            aria-label="Search memories"
            autoComplete="off"
            value={query}
            onChange={handleInputChange}
            onFocus={() => setIsOpen(true)}
            placeholder={placeholder}
            className={`
              w-full pl-12 pr-12 py-3 rounded-xl border-2 transition-all duration-200
              bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400
              ${isOpen || query
                ? 'border-blue-500 shadow-lg shadow-blue-500/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
              }
            `}
          />

          {query && (
            <button
              type="button"
              onClick={clearQuery}
              aria-label="Clear search"
              className="absolute right-4 top-1/2 -translate-y-1/2 p-1 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
            >
              <X size={18} className="text-gray-400" />
            </button>
          )}
        </div>
      </form>

      {/* Dropdown panel */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-800 rounded-xl shadow-2xl border border-gray-200 dark:border-gray-700 z-50 max-h-96 overflow-y-auto animate-slideDown">
          {loading ? (
            <div className="p-8 text-center">
              <div className="inline-block animate-spin">
                <Search className="w-6 h-6 text-blue-600" />
              </div>
              <p className="text-gray-600 dark:text-gray-400 mt-2">Searching…</p>
            </div>
          ) : query ? (
            results.length > 0 ? (
              <div className="p-2">
                <p className="px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                  Search Results
                </p>
                {results.map((result) => (
                  <button
                    key={result.id}
                    onClick={() => handleSelectResult(result)}
                    className="w-full text-left px-4 py-3 hover:bg-gray-100 dark:hover:bg-gray-700 transition rounded-lg flex items-start gap-3 group"
                  >
                    <span className="text-lg">{result.icon}</span>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 line-clamp-1">
                        {result.title}
                      </p>
                      {result.description && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-1">
                          {result.description}
                        </p>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center">
                <p className="text-gray-600 dark:text-gray-400">No results found</p>
                <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">Try a different search query</p>
              </div>
            )
          ) : (
            <div className="p-4 space-y-4">
              {/* Quick filters */}
              <div>
                <p className="px-4 py-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                  Quick Filters
                </p>
                <div className="grid grid-cols-2 gap-2 px-2">
                  <Link href="/search?filter=memories" className="p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center gap-2 group">
                    <BookOpen size={16} className="text-blue-600 group-hover:text-blue-700" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">Memories</span>
                  </Link>
                  <Link href="/search?filter=collections" className="p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center gap-2 group">
                    <FolderOpen size={16} className="text-purple-600 group-hover:text-purple-700" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">Collections</span>
                  </Link>
                  <Link href="/discover" className="p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center gap-2 group">
                    <Compass size={16} className="text-green-600 group-hover:text-green-700" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">Discover</span>
                  </Link>
                  <button onClick={() => setQuery('#')} className="p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center gap-2 group">
                    <Zap size={16} className="text-orange-600 group-hover:text-orange-700" />
                    <span className="text-sm font-medium text-gray-900 dark:text-white">Topics</span>
                  </button>
                </div>
              </div>

              {/* Recent searches */}
              {recentSearches.length > 0 && (
                <div>
                  <div className="px-4 py-2 flex items-center justify-between">
                    <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase">
                      Recent Searches
                    </p>
                    <button
                      onClick={() => {
                        setRecentSearches([]);
                        localStorage.removeItem('recentSearches');
                      }}
                      className="text-xs text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition"
                    >
                      Clear
                    </button>
                  </div>
                  <div className="space-y-1 px-2">
                    {recentSearches.slice(0, 5).map((search, index) => (
                      <button
                        key={index}
                        onClick={() => {
                          setQuery(search.query);
                          handleSearch(search.query);
                        }}
                        className="w-full text-left px-4 py-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition flex items-center gap-2 group"
                      >
                        <Clock size={14} className="text-gray-400 group-hover:text-gray-600 dark:group-hover:text-gray-300" />
                        <span className="text-sm text-gray-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400">
                          {search.query}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
