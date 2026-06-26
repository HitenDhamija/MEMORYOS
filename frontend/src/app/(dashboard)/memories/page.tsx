/**
 * Memories Page - Apple Design Language
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import memoryService, { Memory } from '@/services/memoryService';
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

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

export default function MemoriesPage() {
  const { isAuthenticated } = useAuth();
  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [selectedFileType, setSelectedFileType] = useState<string | null>(null);

  const [showUploadModal, setShowUploadModal] = useState(false);
  const [stats, setStats] = useState<StorageStats | null>(null);
  const [successMessage, setSuccessMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');

  const fetchMemories = async (page: number = 1) => {
    setIsLoading(true);
    try {
      const skip = (page - 1) * pageSize;
      let response;
      if (searchQuery || selectedTags.length > 0 || selectedFileType) {
        response = await memoryService.searchMemories({ query: searchQuery || undefined, tags: selectedTags.length > 0 ? selectedTags : undefined, file_type: selectedFileType || undefined, skip, limit: pageSize });
      } else {
        response = await memoryService.listMemories(skip, pageSize);
      }
      setMemories(response.items);
      setTotalCount(response.total);
      setCurrentPage(page);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Failed to load memories');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const summary = await memoryService.getStorageSummary();
      setStats(summary);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  useEffect(() => {
    if (isAuthenticated) { fetchMemories(1); fetchStats(); }
  }, [isAuthenticated]);

  const handleSearch = (query: string, tags: string[], fileType: string | null) => {
    setSearchQuery(query);
    setSelectedTags(tags);
    setSelectedFileType(fileType);
    setCurrentPage(1);
    (async () => {
      setIsLoading(true);
      try {
        let response;
        if (query || tags.length > 0 || fileType) {
          response = await memoryService.searchMemories({ query: query || undefined, tags: tags.length > 0 ? tags : undefined, file_type: fileType || undefined, skip: 0, limit: pageSize });
        } else {
          response = await memoryService.listMemories(0, pageSize);
        }
        setMemories(response.items);
        setTotalCount(response.total);
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : 'Failed to search memories');
      } finally {
        setIsLoading(false);
      }
    })();
  };

  const handleUploadSuccess = () => {
    setShowUploadModal(false);
    setSuccessMessage('Memory uploaded successfully!');
    setTimeout(() => setSuccessMessage(''), 3000);
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
      <div className="min-h-screen">
        {/* Header - Light Tile */}
        <section className="apple-tile-light">
          <div className="max-w-[980px] mx-auto">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-apple-display-lg text-apple-ink">Memory Library</h1>
                <p className="text-apple-body text-apple-ink-48 mt-1">Store and organize your personal knowledge assets</p>
              </div>
              <button onClick={() => setShowUploadModal(!showUploadModal)} className="apple-btn-primary">
                <Upload className="h-5 w-5 mr-2" />
                Upload Memory
              </button>
            </div>
          </div>
        </section>

        {/* Main Content - Parchment Tile */}
        <section className="apple-tile-parchment">
          <div className="max-w-[980px] mx-auto">
            {/* Messages */}
            {successMessage && (
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-apple-sm flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1"><p className="text-apple-caption text-green-800">{successMessage}</p></div>
                <button onClick={() => setSuccessMessage('')} className="text-green-600 hover:text-green-800"><X className="h-5 w-5" /></button>
              </div>
            )}
            {errorMessage && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-apple-sm flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1"><p className="text-apple-caption text-red-800">{errorMessage}</p></div>
                <button onClick={() => setErrorMessage('')} className="text-red-600 hover:text-red-800"><X className="h-5 w-5" /></button>
              </div>
            )}

            {/* Upload Modal */}
            {showUploadModal && (
              <div className="mb-8 apple-utility-card">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-apple-body-strong text-apple-ink">Upload New Memory</h2>
                  <button onClick={() => setShowUploadModal(false)} className="text-apple-ink-48 hover:text-apple-ink"><X className="h-5 w-5" /></button>
                </div>
                <MemoryUploadZone onUploadSuccess={handleUploadSuccess} onUploadError={handleUploadError} />
              </div>
            )}

            {/* Stats */}
            {stats && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                {[
                  { label: 'Total Files', value: stats.total_files },
                  { label: 'Storage Used', value: formatFileSize(stats.total_size) },
                  { label: 'File Types', value: Object.keys(stats.file_types).length },
                  { label: 'Tags', value: stats.tags.length },
                ].map((stat, i) => (
                  <div key={i} className="apple-utility-card">
                    <p className="text-apple-caption text-apple-ink-48 mb-1">{stat.label}</p>
                    <p className="text-apple-display-md text-apple-ink">{stat.value}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Search & Filter */}
            <div className="mb-8">
              <MemorySearchFilter allTags={stats?.tags || []} allFileTypes={stats?.file_types || {}} onSearch={handleSearch} isLoading={isLoading} />
            </div>

            {/* Memory Library */}
            <MemoryLibrary memories={memories} isLoading={isLoading} totalCount={totalCount} currentPage={currentPage} pageSize={pageSize} onPageChange={handlePageChange} onMemoryDeleted={handleMemoryDeleted} onMemoryUpdated={handleMemoryUpdated} />
          </div>
        </section>
      </div>
    </ProtectedRoute>
  );
}
