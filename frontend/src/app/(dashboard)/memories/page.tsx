'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import memoryService, { Memory, MemorySearchParams } from '@/services/memoryService';
import MemoryUploadZone from '@/components/memories/MemoryUploadZone';
import MemoryLibrary from '@/components/memories/MemoryLibrary';
import MemorySearchFilter from '@/components/memories/MemorySearchFilter';
import { AlertCircle, CheckCircle, Upload, X } from 'lucide-react';

interface StorageStats {
  total_size: number;
  total_files: number;
  file_types: Record<string, number>;
  tags: string[];
}

// Helper functions
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

export default function MemoriesPage() {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();

  // State
  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedFileType, setSelectedFileType] = useState<string | null>(null);

  // UI state
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [stats, setStats] = useState<StorageStats | null>(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  // Fetch memories based on search/filter
  const fetchMemories = async (page: number = 1) => {
    setIsLoading(true);
    try {
      const skip = (page - 1) * pageSize;

      let response;
      if (searchQuery || selectedTags.length > 0 || selectedFileType) {
        response = await memoryService.searchMemories({
          query: searchQuery || undefined,
          tags: selectedTags.length > 0 ? selectedTags : undefined,
          file_type: selectedFileType || undefined,
          skip,
          limit: pageSize,
        });
      } else {
        response = await memoryService.listMemories(skip, pageSize);
      }

      setMemories(response.items);
      setTotalCount(response.total);
      setCurrentPage(page);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Failed to load memories'
      );
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch storage stats
  const fetchStats = async () => {
    try {
      const summary = await memoryService.getStorageSummary();
      setStats(summary);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  // Initial load
  useEffect(() => {
    if (isAuthenticated) {
      fetchMemories(1);
      fetchStats();
    }
  }, [isAuthenticated]);

  // Handle search/filter changes (reset to page 1)
  const handleSearch = (query: string, tags: string[], fileType: string | null) => {
    setSearchQuery(query);
    setSelectedTags(tags);
    setSelectedFileType(fileType);
    setCurrentPage(1);

    // Fetch with new filters
    const skip = 0;
    (async () => {
      setIsLoading(true);
      try {
        let response;
        if (query || tags.length > 0 || fileType) {
          response = await memoryService.searchMemories({
            query: query || undefined,
            tags: tags.length > 0 ? tags : undefined,
            file_type: fileType || undefined,
            skip,
            limit: pageSize,
          });
        } else {
          response = await memoryService.listMemories(skip, pageSize);
        }

        setMemories(response.items);
        setTotalCount(response.total);
      } catch (error) {
        setErrorMessage(
          error instanceof Error ? error.message : 'Failed to search memories'
        );
      } finally {
        setIsLoading(false);
      }
    })();
  };

  const handleUploadSuccess = () => {
    setShowUploadModal(false);
    setSuccessMessage('Memory uploaded successfully! 🎉');
    setTimeout(() => setSuccessMessage(''), 3000);

    // Refresh memories and stats
    fetchMemories(1);
    fetchStats();
  };

  const handleUploadError = (error: string) => {
    setErrorMessage(error);
    setTimeout(() => setErrorMessage(''), 5000);
  };

  const handleMemoryDeleted = () => {
    setSuccessMessage('Memory deleted successfully');
    setTimeout(() => setSuccessMessage(''), 3000);
    fetchMemories(currentPage);
    fetchStats();
  };

  const handleMemoryUpdated = () => {
    setSuccessMessage('Memory updated successfully');
    setTimeout(() => setSuccessMessage(''), 3000);
    fetchMemories(currentPage);
    fetchStats();
  };

  const handlePageChange = (page: number) => {
    fetchMemories(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 sticky top-0 z-40">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
                  Memory Library
                </h1>
                <p className="text-gray-600 text-sm sm:text-base mt-1">
                  Store and organize your personal knowledge assets
                </p>
              </div>

              <button
                onClick={() => setShowUploadModal(!showUploadModal)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium transition-colors"
              >
                <Upload className="h-5 w-5" />
                <span className="hidden sm:inline">Upload Memory</span>
              </button>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Messages */}
          {successMessage && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-800">{successMessage}</p>
              </div>
              <button
                onClick={() => setSuccessMessage('')}
                className="text-green-600 hover:text-green-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}

          {errorMessage && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm font-medium text-red-800">{errorMessage}</p>
              </div>
              <button
                onClick={() => setErrorMessage('')}
                className="text-red-600 hover:text-red-800"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
          )}

          {/* Upload Modal */}
          {showUploadModal && (
            <div className="mb-8 p-6 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Upload New Memory</h2>
                <button
                  onClick={() => setShowUploadModal(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
              <MemoryUploadZone
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
              />
            </div>
          )}

          {/* Stats */}
          {stats && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-600 mb-1">Total Files</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total_files}</p>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-600 mb-1">Storage Used</p>
                <p className="text-2xl font-bold text-gray-900">
                  {formatFileSize(stats.total_size)}
                </p>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-600 mb-1">File Types</p>
                <p className="text-2xl font-bold text-gray-900">
                  {Object.keys(stats.file_types).length}
                </p>
              </div>
              <div className="bg-white rounded-lg border border-gray-200 p-4">
                <p className="text-sm text-gray-600 mb-1">Tags</p>
                <p className="text-2xl font-bold text-gray-900">{stats.tags.length}</p>
              </div>
            </div>
          )}

          {/* Search & Filter */}
          <div className="mb-8">
            <MemorySearchFilter
              allTags={stats?.tags || []}
              allFileTypes={stats?.file_types || {}}
              onSearch={handleSearch}
              isLoading={isLoading}
            />
          </div>

          {/* Memory Library */}
          <MemoryLibrary
            memories={memories}
            isLoading={isLoading}
            totalCount={totalCount}
            currentPage={currentPage}
            pageSize={pageSize}
            onPageChange={handlePageChange}
            onMemoryDeleted={handleMemoryDeleted}
            onMemoryUpdated={handleMemoryUpdated}
          />
        </div>
      </div>
    </ProtectedRoute>
  );
}
