'use client';

import React, { useState } from 'react';
import { Search, Loader2, AlertCircle, ExternalLink } from 'lucide-react';
import { useSemanticSearch } from '@/hooks/useDiscovery';
import Link from 'next/link';

export default function SemanticSearchComponent() {
  const [query, setQuery] = useState('');
  const { results, loading, error, search, reset } = useSemanticSearch();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      search(query);
    }
  };

  const handleClear = () => {
    setQuery('');
    reset();
  };

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm p-6 border border-slate-200 dark:border-slate-700">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400 dark:text-slate-600" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by meaning... e.g., 'machine learning', 'productivity tips', 'climate data'"
              className="w-full pl-10 pr-4 py-3 border border-slate-300 dark:border-slate-600 rounded-lg bg-white dark:bg-slate-700 text-slate-900 dark:text-white placeholder-slate-500 dark:placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div className="flex gap-3">
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-700 dark:hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              Search
            </button>
            {query && (
              <button
                type="button"
                onClick={handleClear}
                className="px-6 py-2 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 rounded-lg font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors"
              >
                Clear
              </button>
            )}
          </div>
        </form>

        {/* Search Tips */}
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded text-sm text-blue-700 dark:text-blue-300">
          <p className="font-medium mb-1">💡 Tip:</p>
          <p>
            Semantic search understands meaning, not just keywords. Try searching for topics, concepts, or ideas from your memories.
          </p>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
          <div>
            <h3 className="font-medium text-red-900 dark:text-red-200">Search Error</h3>
            <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600 dark:text-blue-400 mr-2" />
          <span className="text-slate-600 dark:text-slate-400">
            Searching your memories...
          </span>
        </div>
      )}

      {/* Results */}
      {results && !loading && (
        <div>
          <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-blue-900 dark:text-blue-200">
              Found <span className="font-semibold">{results.total_results}</span> results for "
              <span className="italic">{results.query}</span>"
            </p>
          </div>

          {results.total_results > 0 ? (
            <div className="space-y-3">
              {results.results.map((result) => (
                <Link
                  key={result.memory_id}
                  href={`/memories/${result.memory_id}`}
                >
                  <div className="group bg-white dark:bg-slate-800 rounded-lg shadow-sm p-4 border border-slate-200 dark:border-slate-700 hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-md transition-all">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="font-medium text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                        {result.filename}
                      </h3>
                      <ExternalLink className="w-4 h-4 text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors" />
                    </div>

                    {/* Similarity Score */}
                    <div className="flex items-center gap-2 mt-3">
                      <div className="flex-1 bg-slate-200 dark:bg-slate-700 rounded-full h-2 max-w-xs">
                        <div
                          className="bg-green-500 h-2 rounded-full transition-all"
                          style={{
                            width: `${Math.round(result.similarity_score * 100)}%`,
                          }}
                        />
                      </div>
                      <span className="text-sm text-slate-600 dark:text-slate-400">
                        {Math.round(result.similarity_score * 100)}% match
                      </span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-12 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <p className="text-slate-500 dark:text-slate-400">
                No results found. Try a different search term.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Empty State */}
      {!results && !loading && query && (
        <div className="text-center py-12 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
          <p className="text-slate-500 dark:text-slate-400">
            Ready to search. Click the Search button to find related memories.
          </p>
        </div>
      )}
    </div>
  );
}
