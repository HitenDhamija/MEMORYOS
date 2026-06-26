/**
 * Memory Library - Apple Design Language
 */

'use client';

import React from 'react';
import { Memory } from '@/services/memoryService';
import MemoryCard from './MemoryCard';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface MemoryLibraryProps {
  memories: Memory[];
  isLoading: boolean;
  totalCount: number;
  currentPage: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onMemoryDeleted: () => void;
  onMemoryUpdated: () => void;
}

export default function MemoryLibrary({ memories, isLoading, totalCount, currentPage, pageSize, onPageChange, onMemoryDeleted, onMemoryUpdated }: MemoryLibraryProps) {
  const totalPages = Math.ceil(totalCount / pageSize);
  const hasNextPage = currentPage < totalPages;
  const hasPrevPage = currentPage > 1;

  if (isLoading && memories.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-apple-blue mb-4"></div>
          <p className="text-apple-body text-apple-ink-48">Loading memories…</p>
        </div>
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <p className="text-apple-body text-apple-ink mb-2">No memories yet</p>
          <p className="text-apple-caption text-apple-ink-48">Upload a file or adjust your filters to get started</p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {memories.map((memory) => (
          <MemoryCard key={memory.id} memory={memory} onDelete={onMemoryDeleted} onUpdate={onMemoryUpdated} />
        ))}
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between py-4 border-t border-apple-hairline pt-6">
          <div className="text-apple-caption text-apple-ink-48">Page {currentPage} of {totalPages} ({totalCount} total)</div>
          <div className="flex gap-2">
            <button onClick={() => onPageChange(currentPage - 1)} disabled={!hasPrevPage || isLoading} className="apple-btn-secondary disabled:opacity-50" aria-label="Previous page">
              <ChevronLeft className="h-4 w-4" /> <span className="hidden sm:inline">Previous</span>
            </button>
            <div className="flex gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                if (page === currentPage || page === currentPage - 1 || page === currentPage + 1 || page === 1 || page === totalPages) {
                  return (
                    <button key={page} onClick={() => onPageChange(page)} disabled={isLoading} className={`h-10 w-10 rounded-apple-sm border transition-colors ${page === currentPage ? 'bg-apple-blue text-white border-apple-blue' : 'border-apple-hairline bg-apple-canvas hover:bg-apple-parchment'}`}>
                      {page}
                    </button>
                  );
                }
                if (page === currentPage - 2 || page === currentPage + 2) {
                  return <span key={`ellipsis-${page}`} className="flex items-center px-2" aria-hidden="true">…</span>;
                }
                return null;
              })}
            </div>
            <button onClick={() => onPageChange(currentPage + 1)} disabled={!hasNextPage || isLoading} className="apple-btn-secondary disabled:opacity-50" aria-label="Next page">
              <span className="hidden sm:inline">Next</span> <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
