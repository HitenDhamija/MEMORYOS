'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { Search as SearchIcon, FileText, Loader2, Clock, Tag, ArrowRight } from 'lucide-react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import discoveryService, { SearchResult } from '@/services/discoveryService';
import memoryService, { Memory } from '@/services/memoryService';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [recentMemories, setRecentMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [recentLoading, setRecentLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const loadRecent = async () => {
      try {
        const data = await memoryService.listMemories(0, 6);
        setRecentMemories(data.items || []);
      } catch {
      } finally {
        setRecentLoading(false);
      }
    };
    loadRecent();
  }, []);

  const handleSearch = useCallback(async (searchQuery?: string) => {
    const q = (searchQuery || query).trim();
    if (!q) return;

    setLoading(true);
    setSearched(true);
    try {
      const response = await discoveryService.semanticSearch(q, 20, 0.1);
      setResults(response.results || []);
    } catch (error) {
      console.error('Search failed:', error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [query]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSearch();
  };

  const formatScore = (score: number) => `${Math.round(score * 100)}%`;

  return (
    <ProtectedRoute>
      <div className="-mx-6 -mt-4">
        <section className="bg-white border-b border-gray-200">
          <div className="max-w-[720px] mx-auto text-center py-12 px-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Search</h1>
            <p className="text-gray-500 mb-8">Find your memories with semantic search</p>
            <div className="relative">
              <SearchIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search your knowledge…"
                className="w-full pl-12 pr-28 h-14 border border-gray-300 rounded-full text-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
              />
              <button
                onClick={() => handleSearch()}
                disabled={!query.trim() || loading}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-6 h-10 bg-gray-900 text-white text-sm font-medium rounded-full hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Search'}
              </button>
            </div>
          </div>
        </section>

        <section className="py-8 px-6">
          <div className="max-w-[980px] mx-auto">
            {loading && (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
              </div>
            )}

            {searched && !loading && results.length === 0 && (
              <div className="text-center py-20">
                <SearchIcon className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500 text-lg">No results found for "{query}"</p>
                <p className="text-gray-400 text-sm mt-2">Try different keywords or upload more memories</p>
              </div>
            )}

            {searched && !loading && results.length > 0 && (
              <div>
                <p className="text-sm text-gray-500 mb-6">{results.length} result{results.length !== 1 ? 's' : ''} for "<span className="font-medium text-gray-700">{query}</span>"</p>
                <div className="space-y-3">
                  {results.map((result, idx) => (
                    <div
                      key={`${result.memory_id}-${idx}`}
                      onClick={() => router.push(`/memories/${result.memory_id}`)}
                      className="group flex items-center gap-4 p-4 bg-white border border-gray-200 rounded-xl hover:border-gray-300 hover:shadow-sm cursor-pointer transition"
                    >
                      <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center shrink-0">
                        <FileText className="w-5 h-5 text-gray-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate group-hover:text-blue-600 transition">{result.filename}</p>
                        <p className="text-xs text-gray-400 mt-0.5">Memory #{result.memory_id}</p>
                      </div>
                      <div className="text-right shrink-0">
                        <span className="text-xs font-semibold text-blue-600 bg-blue-50 px-2 py-1 rounded-full">{formatScore(result.similarity_score)}</span>
                        <p className="text-[10px] text-gray-400 mt-1">match</p>
                      </div>
                      <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 shrink-0 transition" />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!searched && (
              <div>
                {recentLoading ? (
                  <div className="flex items-center justify-center py-20">
                    <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
                  </div>
                ) : recentMemories.length > 0 ? (
                  <div>
                    <h2 className="text-sm font-semibold text-gray-900 mb-4">Recent Memories</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {recentMemories.map(memory => (
                        <div
                          key={memory.id}
                          onClick={() => router.push(`/memories/${memory.id}`)}
                          className="group p-4 bg-white border border-gray-200 rounded-xl hover:border-gray-300 hover:shadow-sm cursor-pointer transition"
                        >
                          <div className="flex items-center gap-3 mb-3">
                            <div className="w-8 h-8 rounded-lg bg-gray-100 flex items-center justify-center">
                              <FileText className="w-4 h-4 text-gray-500" />
                            </div>
                            <p className="text-sm font-medium text-gray-900 truncate group-hover:text-blue-600 transition">{memory.title}</p>
                          </div>
                          {memory.description && (
                            <p className="text-xs text-gray-500 line-clamp-2 mb-3">{memory.description}</p>
                          )}
                          <div className="flex items-center gap-3 text-xs text-gray-400">
                            <span className="flex items-center gap-1"><Clock className="w-3 h-3" />{new Date(memory.upload_date).toLocaleDateString()}</span>
                            {memory.tags && (Array.isArray(memory.tags) ? memory.tags.length > 0 : true) && (
                              <span className="flex items-center gap-1"><Tag className="w-3 h-3" />{Array.isArray(memory.tags) ? memory.tags.length : memory.tags.split(',').length} tags</span>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-20">
                    <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500">No memories yet. Upload some to get started.</p>
                  </div>
                )}
              </div>
            )}
          </div>
        </section>
      </div>
    </ProtectedRoute>
  );
}
