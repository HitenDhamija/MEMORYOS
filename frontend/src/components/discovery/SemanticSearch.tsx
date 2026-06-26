/**
 * Semantic Search - Apple Design Language
 */

'use client';

import React, { useState } from 'react';
import { Search, Loader2, AlertCircle, ExternalLink } from 'lucide-react';
import { useSemanticSearch } from '@/hooks/useDiscovery';
import Link from 'next/link';

export default function SemanticSearchComponent() {
  const [query, setQuery] = useState('');
  const { results, loading, error, search, reset } = useSemanticSearch();

  const handleSearch = (e: React.FormEvent) => { e.preventDefault(); if (query.trim()) search(query); };
  const handleClear = () => { setQuery(''); reset(); };

  return (
    <div className="space-y-6">
      <div className="apple-utility-card">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-apple-ink-48" />
            <input type="text" name="semantic-search" aria-label="Search by meaning" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search by meaning… e.g., 'machine learning', 'productivity tips'" className="apple-search-input pl-10" />
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={loading || !query.trim()} className="apple-btn-primary disabled:opacity-50 flex items-center gap-2">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />} Search
            </button>
            {query && <button type="button" onClick={handleClear} className="apple-btn-secondary">Clear</button>}
          </div>
        </form>
        <div className="mt-4 p-3 bg-apple-blue/5 border border-apple-blue/20 rounded-apple-sm text-apple-caption text-apple-blue">
          <p className="font-medium mb-1">Tip:</p>
          <p>Semantic search understands meaning, not just keywords. Try searching for topics, concepts, or ideas.</p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-apple-sm flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
          <div><h3 className="font-medium text-red-900">Search Error</h3><p className="text-red-700 text-apple-caption">{error}</p></div>
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-apple-blue mr-2" />
          <span className="text-apple-body text-apple-ink-48">Searching your memories…</span>
        </div>
      )}

      {results && !loading && (
        <div>
          <div className="mb-6 p-4 bg-apple-blue/5 border border-apple-blue/20 rounded-apple-sm">
            <p className="text-apple-blue">Found <span className="font-semibold">{results.total_results}</span> results for "<span className="italic">{results.query}</span>"</p>
          </div>
          {results.total_results > 0 ? (
            <div className="space-y-3">
              {results.results.map((result) => (
                <Link key={result.memory_id} href={`/memories/${result.memory_id}`}>
                  <div className="group apple-utility-card hover:border-apple-blue transition-all">
                    <div className="flex items-start justify-between mb-2">
                      <h3 className="text-apple-body-strong text-apple-ink group-hover:text-apple-blue transition-colors">{result.filename}</h3>
                      <ExternalLink className="w-4 h-4 text-apple-ink-48 group-hover:text-apple-blue transition-colors" />
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                      <div className="flex-1 bg-apple-parchment rounded-full h-2 max-w-xs">
                        <div className="bg-apple-blue h-2 rounded-full transition-all" style={{ width: `${Math.round(result.similarity_score * 100)}%` }} />
                      </div>
                      <span className="text-apple-caption text-apple-ink-48">{Math.round(result.similarity_score * 100)}% match</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-12"><p className="text-apple-body text-apple-ink-48">No results found. Try a different search term.</p></div>
          )}
        </div>
      )}

      {!results && !loading && query && (
        <div className="text-center py-12"><p className="text-apple-body text-apple-ink-48">Ready to search. Click Search to find related memories.</p></div>
      )}
    </div>
  );
}
