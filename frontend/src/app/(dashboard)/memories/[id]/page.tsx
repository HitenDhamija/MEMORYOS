'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Loader2, AlertCircle, Download, Trash2, Link2, Zap } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import { useMemoryRecommendations } from '@/hooks/useDiscovery';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import memoryService, { Memory } from '@/services/memoryService';
import Link from 'next/link';

interface MemoryDetails extends Memory {
  processing_status?: string;
  extracted_text?: string;
  language?: string;
  topics?: Record<string, unknown>;
  word_count?: number;
}

export default function MemoryDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  
  const memoryId = parseInt(params.id as string);
  const { recommendations, loading: recommendationsLoading } = useMemoryRecommendations(memoryId);

  const [memory, setMemory] = useState<MemoryDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadMemory = async () => {
      try {
        setLoading(true);
        const data = await memoryService.getMemory(memoryId);
        setMemory(data as MemoryDetails);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load memory');
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      loadMemory();
    }
  }, [memoryId, isAuthenticated]);

  const handleDownload = async () => {
    try {
      if (!memory) return;
      const url = await memoryService.downloadMemory(memoryId);
      const link = document.createElement('a');
      link.href = url;
      link.download = memory.filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this memory?')) return;
    
    try {
      await memoryService.deleteMemory(memoryId);
      router.push('/memories');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  if (!isAuthenticated) {
    return <ProtectedRoute><div /></ProtectedRoute>;
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 flex items-center justify-center">
        <div className="flex items-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-blue-600 dark:text-blue-400" />
          <span className="text-slate-600 dark:text-slate-400">Loading memory details...</span>
        </div>
      </div>
    );
  }

  if (error || !memory) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-4">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => router.back()}
            className="mb-4 flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-medium text-red-900 dark:text-red-200">Error</h3>
              <p className="text-red-700 dark:text-red-300 text-sm">{error || 'Memory not found'}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Header */}
      <div className="border-b border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <button
            onClick={() => router.back()}
            className="mb-4 flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2">{memory.filename}</h1>
          <p className="text-slate-600 dark:text-slate-400">
            Uploaded {new Date(memory.upload_date).toLocaleDateString()}
          </p>
        </div>
      </div>

      {/* Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Memory Info */}
        <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6 mb-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Status</p>
              <p className="font-medium text-slate-900 dark:text-white capitalize">
                {memory.processing_status || memory.status}
              </p>
            </div>
            <div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">File Size</p>
              <p className="font-medium text-slate-900 dark:text-white">
                {(memory.file_size / 1024).toFixed(1)} KB
              </p>
            </div>
            {memory.language && (
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Language</p>
                <p className="font-medium text-slate-900 dark:text-white capitalize">{memory.language}</p>
              </div>
            )}
            {memory.word_count && (
              <div>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">Words</p>
                <p className="font-medium text-slate-900 dark:text-white">{memory.word_count}</p>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={handleDownload}
              className="px-4 py-2 bg-blue-600 dark:bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors flex items-center gap-2"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
            <button
              onClick={handleDelete}
              className="px-4 py-2 border border-red-300 dark:border-red-800 text-red-600 dark:text-red-400 rounded-lg font-medium hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors flex items-center gap-2"
            >
              <Trash2 className="w-4 h-4" />
              Delete
            </button>
          </div>
        </div>

        {/* Related Memories */}
        {recommendations && recommendations.related_memories.length > 0 && (
          <div className="bg-white dark:bg-slate-800 rounded-lg shadow-sm border border-slate-200 dark:border-slate-700 p-6">
            <div className="flex items-center gap-2 mb-4">
              <Link2 className="w-5 h-5 text-blue-600 dark:text-blue-400" />
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                Related Memories
              </h2>
            </div>

            <div className="space-y-3">
              {recommendations.related_memories.map((related) => (
                <Link
                  key={related.memory_id}
                  href={`/memories/${related.memory_id}`}
                >
                  <div className="group flex items-start justify-between p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg border border-slate-200 dark:border-slate-600 hover:border-blue-300 dark:hover:border-blue-600 hover:bg-blue-50 dark:hover:bg-slate-700 transition-all">
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 line-clamp-1 transition-colors">
                        {related.filename}
                      </h3>
                      <div className="flex items-center gap-2 mt-2">
                        <div className="flex-1 bg-slate-200 dark:bg-slate-600 rounded-full h-2 max-w-xs">
                          <div
                            className="bg-gradient-to-r from-green-400 to-emerald-400 h-2 rounded-full transition-all"
                            style={{
                              width: `${Math.round(related.similarity_score * 100)}%`,
                            }}
                          />
                        </div>
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {Math.round(related.similarity_score * 100)}% match
                        </span>
                      </div>
                    </div>
                    <Zap className="w-4 h-4 text-blue-600 dark:text-blue-400 ml-2 flex-shrink-0 mt-1" />
                  </div>
                </Link>
              ))}
            </div>

            <Link
              href="/discover"
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-medium transition-colors"
            >
              <Zap className="w-4 h-4" />
              Discover more connections
            </Link>
          </div>
        )}

        {recommendationsLoading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 animate-spin text-blue-600 dark:text-blue-400 mr-2" />
            <span className="text-slate-600 dark:text-slate-400">Loading related memories...</span>
          </div>
        )}
      </main>
    </div>
  );
}
