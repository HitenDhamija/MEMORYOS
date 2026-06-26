/**
 * Collections Page - Apple Design Language
 */

'use client';

import React, { useState, useEffect } from 'react';
import { FolderPlus, Loader2, AlertCircle, Search, Grid, List, Sparkles, X } from 'lucide-react';
import { useCollections, useSuggestions, useCollectionStats } from '@/hooks/useCollections';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import CreateCollectionDialog from '@/components/collections/CreateCollectionDialog';
import CollectionsGrid from '@/components/collections/CollectionsGrid';
import SuggestionsPanel from '@/components/collections/SuggestionsPanel';
import CollectionStatsCard from '@/components/collections/CollectionStatsCard';

export default function CollectionsPage() {
  const { collections, loading, error, createCollection, deleteCollection, fetchCollections } = useCollections();
  const { suggestions, loading: suggestionsLoading, fetchSuggestions, generateSuggestions, acceptSuggestion, rejectSuggestion } = useSuggestions();
  const { stats, loading: statsLoading, refetch: refetchStats } = useCollectionStats();
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [searchQuery, setSearchQuery] = useState('');
  const [generating, setGenerating] = useState(false);

  // Fetch pending suggestions on mount
  useEffect(() => {
    fetchSuggestions();
  }, []);

  const handleDelete = async (id: number) => {
    await deleteCollection(id);
    refetchStats();
  };

  const filteredCollections = collections.filter((c) => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (c.description && c.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleCreate = async (name: string, description?: string, color?: string, icon?: string) => {
    await createCollection(name, description, color, icon);
    await fetchCollections();
    refetchStats();
  };

  const handleGenerateSuggestions = async () => {
    setGenerating(true);
    try {
      await generateSuggestions();
    } finally {
      setGenerating(false);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <div className="bg-white border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-xl">
                    <FolderPlus className="w-6 h-6 text-blue-600" />
                  </div>
                  Collections
                </h1>
                <p className="text-sm text-gray-500 mt-1 ml-11">
                  Organize your memories into personalized collections
                </p>
              </div>
              <button 
                onClick={() => setShowCreateDialog(true)} 
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors shadow-sm"
              >
                <FolderPlus className="w-4 h-4" />
                New Collection
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {/* Error Alert */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
              <div className="flex-1">
                <h3 className="font-medium text-red-900">Error loading collections</h3>
                <p className="text-sm text-red-700 mt-1">{error}</p>
              </div>
              <button 
                onClick={() => fetchCollections()}
                className="text-sm text-red-600 hover:text-red-800 font-medium"
              >
                Retry
              </button>
            </div>
          )}

          {/* Stats */}
          {stats && !statsLoading && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <CollectionStatsCard 
                label="Total Collections" 
                value={stats.total_collections} 
                icon="folder"
                color="blue"
              />
              <CollectionStatsCard 
                label="Average Size" 
                value={Math.round(stats.average_size)} 
                icon="layers"
                color="purple"
              />
              {stats.largest_collection && (
                <CollectionStatsCard 
                  label="Largest" 
                  value={stats.largest_collection.size} 
                  subtext={stats.largest_collection.name} 
                  icon="award"
                  color="green"
                />
              )}
              {stats.recently_updated && (
                <CollectionStatsCard 
                  label="Recently Updated" 
                  value={stats.recently_updated.name} 
                  subtext={new Date(stats.recently_updated.updated_at).toLocaleDateString()}
                  icon="clock"
                  color="orange"
                />
              )}
            </div>
          )}

          {/* Suggestions */}
          {suggestions.length > 0 && (
            <SuggestionsPanel 
              suggestions={suggestions} 
              loading={suggestionsLoading}
              onAccept={acceptSuggestion} 
              onReject={rejectSuggestion} 
            />
          )}

          {/* Search and Controls */}
          <div className="mb-6 bg-white rounded-xl border border-gray-200 p-4">
            <div className="flex flex-col sm:flex-row gap-4 items-stretch sm:items-center">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search collections..."
                  className="w-full pl-10 pr-10 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
              
              {/* Suggestions button */}
              <button 
                onClick={handleGenerateSuggestions} 
                disabled={generating}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors"
              >
                {generating ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
                {generating ? 'Generating...' : 'Get Suggestions'}
              </button>
              
              {/* View Toggle */}
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button 
                  onClick={() => setViewMode('grid')} 
                  className={`p-2 rounded-md transition-all ${
                    viewMode === 'grid' 
                      ? 'bg-white text-blue-600 shadow-sm' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <Grid className="w-5 h-5" />
                </button>
                <button 
                  onClick={() => setViewMode('list')} 
                  className={`p-2 rounded-md transition-all ${
                    viewMode === 'list' 
                      ? 'bg-white text-blue-600 shadow-sm' 
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  <List className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Collections Content */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <Loader2 className="w-10 h-10 animate-spin text-blue-500 mb-4" />
              <span className="text-gray-500">Loading collections...</span>
            </div>
          ) : filteredCollections.length > 0 ? (
            <CollectionsGrid 
              collections={filteredCollections} 
              viewMode={viewMode} 
              onDelete={handleDelete}
            />
          ) : (
            <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <FolderPlus className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                {searchQuery ? 'No collections found' : 'No collections yet'}
              </h3>
              <p className="text-gray-500 mb-6 max-w-sm mx-auto">
                {searchQuery 
                  ? 'No collections match your search. Try different keywords.'
                  : 'Create your first collection to start organizing your memories.'
                }
              </p>
              {!searchQuery && (
                <button 
                  onClick={() => setShowCreateDialog(true)} 
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-lg hover:bg-gray-800 transition-colors"
                >
                  <FolderPlus className="w-4 h-4" />
                  Create Collection
                </button>
              )}
            </div>
          )}
        </div>

        {/* Create Dialog */}
        <CreateCollectionDialog 
          open={showCreateDialog} 
          onClose={() => setShowCreateDialog(false)} 
          onCreate={handleCreate} 
        />
      </div>
    </ProtectedRoute>
  );
}
