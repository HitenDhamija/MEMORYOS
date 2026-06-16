'use client';

import React, { useState, useEffect } from 'react';
import { Loader2, SearchIcon, Zap, AlertCircle } from 'lucide-react';
import { useDiscoveryExplore } from '@/hooks/useDiscovery';
import SemanticSearchComponent from '@/components/discovery/SemanticSearch';
import MemoryConnectionsGrid from '@/components/discovery/MemoryConnectionsGrid';

export default function DiscoverPage() {
  const { discovery, loading, error, explore } = useDiscoveryExplore();
  const [activeTab, setActiveTab] = useState<'explore' | 'search'>('explore');

  useEffect(() => {
    // Load initial discovery on mount
    explore(20, 0.5);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3 mb-2">
            <Zap className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
              Discover Connections
            </h1>
          </div>
          <p className="text-slate-600 dark:text-slate-400">
            Explore semantic relationships and discover related knowledge
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 sticky top-[88px] z-9">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex gap-8">
            <button
              onClick={() => setActiveTab('explore')}
              className={`px-4 py-3 font-medium border-b-2 transition-colors ${
                activeTab === 'explore'
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400'
                  : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4" />
                Explore
              </div>
            </button>
            <button
              onClick={() => setActiveTab('search')}
              className={`px-4 py-3 font-medium border-b-2 transition-colors ${
                activeTab === 'search'
                  ? 'border-blue-600 text-blue-600 dark:text-blue-400 dark:border-blue-400'
                  : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
              }`}
            >
              <div className="flex items-center gap-2">
                <SearchIcon className="w-4 h-4" />
                Search
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Error State */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-medium text-red-900 dark:text-red-200">Error</h3>
              <p className="text-red-700 dark:text-red-300 text-sm">{error}</p>
            </div>
          </div>
        )}

        {/* Explore Tab */}
        {activeTab === 'explore' && (
          <div>
            {loading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 dark:text-blue-400 mr-2" />
                <span className="text-slate-600 dark:text-slate-400">
                  Discovering connections...
                </span>
              </div>
            )}

            {discovery && !loading && (
              <>
                <div className="mb-6">
                  <p className="text-slate-600 dark:text-slate-400 mb-4">
                    Found <span className="font-semibold">{discovery.total_items}</span> memories with related connections
                  </p>
                </div>
                <MemoryConnectionsGrid discoveries={discovery.memories} />
              </>
            )}

            {discovery && discovery.total_items === 0 && !loading && (
              <div className="text-center py-12">
                <p className="text-slate-500 dark:text-slate-400">
                  No connections found yet. Upload more memories to see recommendations.
                </p>
              </div>
            )}
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && <SemanticSearchComponent />}
      </main>
    </div>
  );
}
