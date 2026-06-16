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

export default function MemoryLibrary({
  memories,
  isLoading,
  totalCount,
  currentPage,
  pageSize,
  onPageChange,
  onMemoryDeleted,
  onMemoryUpdated,
}: MemoryLibraryProps) {
  const totalPages = Math.ceil(totalCount / pageSize);
  const hasNextPage = currentPage < totalPages;
  const hasPrevPage = currentPage > 1;

  if (isLoading && memories.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading memories...</p>
        </div>
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <p className="text-gray-500 text-lg mb-2">No memories yet</p>
          <p className="text-gray-400">
            Upload a file or adjust your filters to get started
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Memory Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {memories.map((memory) => (
          <MemoryCard
            key={memory.id}
            memory={memory}
            onDelete={onMemoryDeleted}
            onUpdate={onMemoryUpdated}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between py-4 border-t border-gray-200 pt-6">
          <div className="text-sm text-gray-600">
            Page {currentPage} of {totalPages} ({totalCount} total)
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => onPageChange(currentPage - 1)}
              disabled={!hasPrevPage || isLoading}
              className="flex items-center gap-1 px-3 py-2 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
              <span className="hidden sm:inline">Previous</span>
            </button>

            {/* Page Numbers */}
            <div className="flex gap-1">
              {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => {
                // Show current page and adjacent pages
                if (
                  page === currentPage ||
                  page === currentPage - 1 ||
                  page === currentPage + 1 ||
                  page === 1 ||
                  page === totalPages
                ) {
                  return (
                    <button
                      key={page}
                      onClick={() => onPageChange(page)}
                      disabled={isLoading}
                      className={`h-10 w-10 rounded-lg border transition-colors ${
                        page === currentPage
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'border-gray-300 bg-white hover:bg-gray-50'
                      } disabled:cursor-not-allowed`}
                    >
                      {page}
                    </button>
                  );
                }

                // Show ellipsis
                if (page === currentPage - 2 || page === currentPage + 2) {
                  return (
                    <span key={`ellipsis-${page}`} className="flex items-center px-2">
                      ...
                    </span>
                  );
                }

                return null;
              })}
            </div>

            <button
              onClick={() => onPageChange(currentPage + 1)}
              disabled={!hasNextPage || isLoading}
              className="flex items-center gap-1 px-3 py-2 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span className="hidden sm:inline">Next</span>
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
