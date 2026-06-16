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
    return (
      <div className="text-center py-12 bg-slate-50 dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
        <p className="text-slate-500 dark:text-slate-400">
          No memory connections found. Upload more memories to see recommendations.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {discoveries.map((discovery) => (
        <div
          key={discovery.memory_id}
          className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 overflow-hidden hover:shadow-md transition-shadow"
        >
          {/* Memory Header */}
          <Link href={`/memories/${discovery.memory_id}`}>
            <div className="p-4 bg-gradient-to-r from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-b border-slate-200 dark:border-slate-700 hover:from-blue-100 hover:to-blue-200 dark:hover:from-blue-900/40 dark:hover:to-blue-800/40 transition-colors">
              <h3 className="font-semibold text-slate-900 dark:text-white line-clamp-2">
                {discovery.filename}
              </h3>
            </div>
          </Link>

          {/* Related Memories */}
          <div className="p-4">
            {discovery.related_memories.length > 0 ? (
              <div className="space-y-3">
                <div className="flex items-center gap-2 mb-3">
                  <Link2 className="w-4 h-4 text-blue-600 dark:text-blue-400" />
                  <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                    {discovery.related_memories.length} Related
                  </p>
                </div>

                <div className="space-y-2">
                  {discovery.related_memories.map((related, idx) => (
                    <Link
                      key={`${discovery.memory_id}-${related.memory_id}`}
                      href={`/memories/${related.memory_id}`}
                    >
                      <div className="group flex items-start justify-between p-3 bg-slate-50 dark:bg-slate-700/50 rounded border border-slate-200 dark:border-slate-600 hover:bg-blue-50 dark:hover:bg-slate-700 hover:border-blue-300 dark:hover:border-blue-600 transition-all">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-slate-900 dark:text-white line-clamp-1 group-hover:text-blue-600 dark:group-hover:text-blue-400">
                            {related.filename}
                          </p>
                          <div className="flex items-center gap-2 mt-1">
                            <div className="flex-1 bg-slate-200 dark:bg-slate-600 rounded-full h-1.5 max-w-[80px]">
                              <div
                                className="bg-gradient-to-r from-blue-400 to-cyan-400 h-1.5 rounded-full transition-all"
                                style={{
                                  width: `${Math.round(related.similarity_score * 100)}%`,
                                }}
                              />
                            </div>
                            <span className="text-xs text-slate-500 dark:text-slate-400 whitespace-nowrap">
                              {Math.round(related.similarity_score * 100)}%
                            </span>
                          </div>
                        </div>
                        <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 dark:group-hover:text-blue-400 ml-2 flex-shrink-0 mt-0.5 transition-colors" />
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500 dark:text-slate-400">
                No related memories found
              </p>
            )}
          </div>

          {/* Footer */}
          <Link href={`/memories/${discovery.memory_id}`}>
            <div className="px-4 py-3 bg-slate-50 dark:bg-slate-700/50 border-t border-slate-200 dark:border-slate-700 hover:bg-blue-50 dark:hover:bg-slate-700 transition-colors">
              <p className="text-xs text-blue-600 dark:text-blue-400 font-medium flex items-center gap-1">
                View Details
                <ArrowRight className="w-3 h-3" />
              </p>
            </div>
          </Link>
        </div>
      ))}
    </div>
  );
}
