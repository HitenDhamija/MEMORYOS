/**
 * Discover Page - Apple Design Language
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Loader2, SearchIcon, Zap, AlertCircle } from 'lucide-react';
import { useDiscoveryExplore } from '@/hooks/useDiscovery';
import SemanticSearchComponent from '@/components/discovery/SemanticSearch';
import MemoryConnectionsGrid from '@/components/discovery/MemoryConnectionsGrid';

export default function DiscoverPage() {
  const { discovery, loading, error, explore } = useDiscoveryExplore();
  const [activeTab, setActiveTab] = useState<'explore' | 'search'>('explore');

  useEffect(() => { explore(20, 0.5); }, []);

  return (
    <div className="min-h-screen">
      {/* Header - Light Tile */}
      <section className="apple-tile-light">
        <div className="max-w-[980px] mx-auto">
          <h1 className="text-apple-display-lg text-apple-ink flex items-center gap-3">
            <Zap className="w-8 h-8 text-apple-blue" />
            Discover Connections
          </h1>
          <p className="text-apple-body text-apple-ink-48 mt-1">Explore semantic relationships and discover related knowledge</p>
        </div>
      </section>

      {/* Tabs - Parchment Tile */}
      <section className="apple-tile-parchment border-b border-apple-hairline">
        <div className="max-w-[980px] mx-auto">
          <div className="flex gap-8">
            {[
              { id: 'explore' as const, label: 'Explore', icon: <Zap className="w-4 h-4" /> },
              { id: 'search' as const, label: 'Search', icon: <SearchIcon className="w-4 h-4" /> },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-3 text-apple-body-strong border-b-2 transition-colors ${
                  activeTab === tab.id ? 'border-apple-blue text-apple-blue' : 'border-transparent text-apple-ink-48 hover:text-apple-ink'
                }`}
              >
                <div className="flex items-center gap-2">{tab.icon}{tab.label}</div>
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Content - Light Tile */}
      <section className="apple-tile-light">
        <div className="max-w-[980px] mx-auto">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-apple-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div>
                <h3 className="font-medium text-red-900">Error</h3>
                <p className="text-red-700 text-apple-caption">{error}</p>
              </div>
            </div>
          )}

          {activeTab === 'explore' && (
            <div>
              {loading && (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-apple-blue mr-2" />
                  <span className="text-apple-body text-apple-ink-48">Discovering connections…</span>
                </div>
              )}
              {discovery && !loading && (
                <>
                  <p className="text-apple-body text-apple-ink-48 mb-4">
                    Found <span className="text-apple-body-strong text-apple-ink">{discovery.total_items}</span> memories with related connections
                  </p>
                  <MemoryConnectionsGrid discoveries={discovery.memories} />
                </>
              )}
              {discovery && discovery.total_items === 0 && !loading && (
                <p className="text-apple-body text-apple-ink-48 text-center py-12">No connections found yet. Upload more memories to see recommendations.</p>
              )}
            </div>
          )}
          {activeTab === 'search' && <SemanticSearchComponent />}
        </div>
      </section>
    </div>
  );
}
