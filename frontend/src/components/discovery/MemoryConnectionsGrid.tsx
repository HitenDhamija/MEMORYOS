/**
 * Memory Connections Grid - Apple Design Language
 */

'use client';

import React from 'react';
import { ArrowRight, Link2 } from 'lucide-react';
import Link from 'next/link';
import { DiscoveryItem } from '@/services/discoveryService';

interface MemoryConnectionsGridProps {
  discoveries: DiscoveryItem[];
}

export default function MemoryConnectionsGrid({ discoveries }: MemoryConnectionsGridProps) {
  if (!discoveries || discoveries.length === 0) {
    return <div className="text-center py-12"><p className="text-apple-body text-apple-ink-48">No connections found. Upload more memories to see recommendations.</p></div>;
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {discoveries.map((discovery) => (
        <div key={discovery.memory_id} className="apple-utility-card overflow-hidden hover:border-apple-blue transition-all">
          <Link href={`/memories/${discovery.memory_id}`}>
            <div className="p-4 bg-apple-parchment border-b border-apple-hairline hover:bg-apple-chip/20 transition-colors">
              <h3 className="text-apple-body-strong text-apple-ink line-clamp-2">{discovery.filename}</h3>
            </div>
          </Link>
          <div className="p-4">
            {discovery.related_memories.length > 0 ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 mb-3">
                  <Link2 className="w-4 h-4 text-apple-blue" />
                  <p className="text-apple-caption text-apple-ink">{discovery.related_memories.length} Related</p>
                </div>
                <div className="space-y-2">
                  {discovery.related_memories.map((related) => (
                    <Link key={`${discovery.memory_id}-${related.memory_id}`} href={`/memories/${related.memory_id}`}>
                      <div className="group flex items-start justify-between p-3 rounded-apple-sm border border-apple-hairline hover:border-apple-blue hover:bg-apple-parchment transition-all">
                        <div className="flex-1 min-w-0">
                          <p className="text-apple-caption text-apple-ink line-clamp-1 group-hover:text-apple-blue">{related.filename}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <div className="flex-1 bg-apple-parchment rounded-full h-1.5 max-w-[80px]">
                              <div className="bg-apple-blue h-1.5 rounded-full transition-all" style={{ width: `${Math.round(related.similarity_score * 100)}%` }} />
                            </div>
                            <span className="text-apple-fine-print text-apple-ink-48">{Math.round(related.similarity_score * 100)}%</span>
                          </div>
                        </div>
                        <ArrowRight className="w-4 h-4 text-apple-ink-48 group-hover:text-apple-blue ml-2 flex-shrink-0 mt-0.5 transition-colors" />
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-apple-caption text-apple-ink-48">No related memories found</p>
            )}
          </div>
          <Link href={`/memories/${discovery.memory_id}`}>
            <div className="px-4 py-3 bg-apple-parchment border-t border-apple-hairline hover:bg-apple-chip/20 transition-colors">
              <p className="text-apple-fine-print text-apple-blue font-medium flex items-center gap-1">View Details <ArrowRight className="w-3 h-3" /></p>
            </div>
          </Link>
        </div>
      ))}
    </div>
  );
}
