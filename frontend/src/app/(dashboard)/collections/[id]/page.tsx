/**
 * Collection Details Page - Apple Design Language
 * Enhanced with header, overview, stats, AI summary, timeline, search, sort
 */

'use client';

import React, { useState, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  ArrowLeft, Loader2, AlertCircle, Plus, Trash2, Edit2,
  Search, Grid, List, Clock, SortAsc, SortDesc,
  FileText, Calendar, Tag, CheckSquare
} from 'lucide-react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { useCollectionDetail } from '@/hooks/useCollections';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import collectionsService from '@/services/collectionsService';
import AddMemoriesToCollection from '@/components/collections/AddMemoriesToCollection';

type SortField = 'name' | 'upload_date' | 'status';
type SortOrder = 'asc' | 'desc';
type ViewMode = 'grid' | 'list';

export default function CollectionDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const collectionId = parseInt(params.id as string);
  const { collection, loading, removeMemory } = useCollectionDetail(collectionId);
  
  // Edit mode
  const [editMode, setEditMode] = useState(false);
  const [editName, setEditName] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editing, setEditing] = useState(false);
  
  // View state
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortField, setSortField] = useState<SortField>('upload_date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  
  // Selection state
  const [selectedMemories, setSelectedMemories] = useState<Set<number>>(new Set());
  const [isSelectMode, setIsSelectMode] = useState(false);
  
  // Add memories modal state
  const [showAddMemories, setShowAddMemories] = useState(false);

  React.useEffect(() => {
    if (collection) {
      setEditName(collection.name);
      setEditDescription(collection.description || '');
    }
  }, [collection]);

  // Filtered and sorted memories
  const filteredMemories = useMemo(() => {
    if (!collection?.memories) return [];
    
    let memories = [...collection.memories];
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      memories = memories.filter(m => 
        m.filename?.toLowerCase().includes(query) ||
        m.status?.toLowerCase().includes(query)
      );
    }
    
    // Apply sorting
    memories.sort((a, b) => {
      let comparison = 0;
      switch (sortField) {
        case 'name':
          comparison = (a.filename || '').localeCompare(b.filename || '');
          break;
        case 'upload_date':
          comparison = new Date(a.upload_date).getTime() - new Date(b.upload_date).getTime();
          break;
        case 'status':
          comparison = (a.status || '').localeCompare(b.status || '');
          break;
      }
      return sortOrder === 'asc' ? comparison : -comparison;
    });
    
    return memories;
  }, [collection?.memories, searchQuery, sortField, sortOrder]);

  // Collection stats
  const stats = useMemo(() => {
    if (!collection?.memories) return { total: 0, processed: 0, pending: 0, failed: 0 };
    const memories = collection.memories;
    return {
      total: memories.length,
      processed: memories.filter(m => m.status === 'processed').length,
      pending: memories.filter(m => m.status === 'pending').length,
      failed: memories.filter(m => m.status === 'failed').length,
    };
  }, [collection?.memories]);

  // Timeline data (group by month)
  const timeline = useMemo(() => {
    if (!collection?.memories) return [];
    const grouped: Record<string, number> = {};
    collection.memories.forEach(m => {
      const date = new Date(m.upload_date);
      const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      grouped[key] = (grouped[key] || 0) + 1;
    });
    return Object.entries(grouped)
      .sort(([a], [b]) => b.localeCompare(a))
      .slice(0, 6);
  }, [collection?.memories]);

  const handleUpdateCollection = async () => {
    try {
      setEditing(true);
      await collectionsService.updateCollection(collectionId, { 
        name: editName,
        description: editDescription 
      });
      setEditMode(false);
    } catch (err) {
      alert('Failed to update collection');
    } finally {
      setEditing(false);
    }
  };

  const handleRemoveMemory = async (memoryId: number) => {
    if (!confirm('Remove this memory from the collection?')) return;
    try { await removeMemory(memoryId); } catch (err) { alert('Failed to remove memory'); }
  };

  const handleBulkRemove = async () => {
    if (selectedMemories.size === 0) return;
    if (!confirm(`Remove ${selectedMemories.size} memories from the collection?`)) return;
    
    for (const memoryId of selectedMemories) {
      try { await removeMemory(memoryId); } catch (err) { /* continue */ }
    }
    setSelectedMemories(new Set());
    setIsSelectMode(false);
  };

  const toggleMemorySelection = (memoryId: number) => {
    const newSelection = new Set(selectedMemories);
    if (newSelection.has(memoryId)) {
      newSelection.delete(memoryId);
    } else {
      newSelection.add(memoryId);
    }
    setSelectedMemories(newSelection);
  };

  const toggleSelectAll = () => {
    if (selectedMemories.size === filteredMemories.length) {
      setSelectedMemories(new Set());
    } else {
      setSelectedMemories(new Set(filteredMemories.map(m => m.id)));
    }
  };

  if (!isAuthenticated) return <ProtectedRoute><div /></ProtectedRoute>;

  if (loading) {
    return (
      <div className="apple-tile-light flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-apple-blue" />
          <span className="text-apple-body text-apple-ink-48">Loading collection…</span>
        </div>
      </div>
    );
  }

  if (!collection) {
    return (
      <div className="apple-tile-light p-4 min-h-[60vh]">
        <div className="max-w-[800px] mx-auto">
          <button onClick={() => router.back()} className="mb-4 flex items-center gap-2 apple-link"><ArrowLeft className="w-4 h-4" /> Back</button>
          <div className="p-4 bg-red-50 border border-red-200 rounded-apple-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-medium text-red-900">Error</h3>
              <p className="text-red-700 text-apple-caption">Collection not found</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <>
    <div className="min-h-screen">
      {/* Header Section */}
      <section className="apple-tile-light">
        <div className="max-w-[1200px] mx-auto">
          <button onClick={() => router.back()} className="mb-4 flex items-center gap-2 apple-link transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          
          {/* Cover Image or Color Bar */}
          {collection.cover_image_url ? (
            <div className="relative h-48 rounded-apple-md overflow-hidden mb-4">
              <img src={collection.cover_image_url} alt="" className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
            </div>
          ) : (
            <div 
              className="h-2 rounded-apple-sm mb-4"
              style={{ backgroundColor: `hsl(${['blue', 'red', 'green', 'purple', 'yellow', 'pink', 'indigo', 'cyan'].indexOf(collection.color) * 45}, 70%, 50%)` }}
            />
          )}
          
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {editMode ? (
                <div className="space-y-3">
                  <input 
                    type="text" 
                    value={editName} 
                    onChange={(e) => setEditName(e.target.value)} 
                    className="apple-search-input w-full text-2xl font-semibold" 
                    placeholder="Collection name"
                  />
                  <textarea 
                    value={editDescription} 
                    onChange={(e) => setEditDescription(e.target.value)} 
                    className="apple-search-input w-full h-20 resize-none" 
                    placeholder="Add a description..."
                  />
                  <div className="flex gap-2">
                    <button onClick={handleUpdateCollection} disabled={editing} className="apple-btn-primary disabled:opacity-50">
                      {editing ? 'Saving...' : 'Save'}
                    </button>
                    <button onClick={() => setEditMode(false)} className="apple-btn-secondary">Cancel</button>
                  </div>
                </div>
              ) : (
                <>
                  <h1 className="text-apple-display-lg text-apple-ink mb-2 flex items-center gap-2">
                    {collection.name}
                    <button onClick={() => setEditMode(true)} className="p-2 text-apple-ink-48 hover:text-apple-blue hover:bg-apple-parchment rounded-apple-sm transition-colors">
                      <Edit2 className="w-4 h-4" />
                    </button>
                  </h1>
                  {collection.description && (
                    <p className="text-apple-body text-apple-ink-48">{collection.description}</p>
                  )}
                </>
              )}
            </div>
            
            {/* Action Buttons */}
            <div className="flex items-center gap-2 ml-4">
              <button 
                onClick={() => setIsSelectMode(!isSelectMode)}
                className={`p-2 rounded-apple-sm transition-colors ${isSelectMode ? 'bg-apple-blue text-white' : 'text-apple-ink-48 hover:text-apple-blue hover:bg-apple-parchment'}`}
                title="Select mode"
              >
                <CheckSquare className="w-5 h-5" />
              </button>
              <button 
                onClick={() => setShowAddMemories(true)}
                className="apple-btn-primary inline-flex items-center gap-2"
              >
                <Plus className="w-4 h-4" /> Add Memories
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Stats & Overview Section */}
      <section className="apple-tile-parchment">
        <div className="max-w-[1200px] mx-auto">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'Total Memories', value: stats.total, icon: FileText },
              { label: 'Processed', value: stats.processed, icon: CheckSquare, color: 'text-green-600' },
              { label: 'Pending', value: stats.pending, icon: Clock, color: 'text-yellow-600' },
              { label: 'Failed', value: stats.failed, icon: AlertCircle, color: 'text-red-600' },
            ].map((stat, i) => (
              <div key={i} className="apple-utility-card">
                <div className="flex items-center gap-2 mb-2">
                  <stat.icon className={`w-4 h-4 ${stat.color || 'text-apple-ink-48'}`} />
                  <p className="text-apple-caption text-apple-ink-48">{stat.label}</p>
                </div>
                <p className="text-apple-display-sm text-apple-ink">{stat.value}</p>
              </div>
            ))}
          </div>

          {/* AI Summary Card */}
          <div className="apple-utility-card mb-8">
            <h3 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
              <Tag className="w-4 h-4" />
              Collection Overview
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-apple-ink-48">Created:</span>
                <span className="ml-2 text-apple-ink">{new Date(collection.created_at).toLocaleDateString()}</span>
              </div>
              <div>
                <span className="text-apple-ink-48">Last Updated:</span>
                <span className="ml-2 text-apple-ink">{new Date(collection.updated_at).toLocaleDateString()}</span>
              </div>
              <div>
                <span className="text-apple-ink-48">Color:</span>
                <span className="ml-2 text-apple-ink capitalize">{collection.color}</span>
              </div>
            </div>
          </div>

          {/* Timeline Card */}
          {timeline.length > 0 && (
            <div className="apple-utility-card mb-8">
              <h3 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Upload Timeline
              </h3>
              <div className="flex items-end gap-2 h-24">
                {timeline.map(([month, count]) => {
                  const maxCount = Math.max(...timeline.map(([, c]) => c));
                  const height = maxCount > 0 ? (count / maxCount) * 100 : 0;
                  return (
                    <div key={month} className="flex-1 flex flex-col items-center">
                      <span className="text-xs text-apple-ink-48 mb-1">{count}</span>
                      <div 
                        className="w-full bg-apple-blue rounded-t-sm"
                        style={{ height: `${Math.max(height, 4)}%` }}
                      />
                      <span className="text-xs text-apple-ink-48 mt-1">{month.slice(5)}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Search and Sort Bar */}
          <div className="flex flex-wrap items-center gap-3 mb-6">
            <div className="flex-1 min-w-[200px] relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-apple-ink-48" />
              <input
                type="text"
                placeholder="Search in collection..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="apple-search-input pl-10 w-full"
              />
            </div>
            
            <div className="flex items-center gap-2">
              <select
                value={sortField}
                onChange={(e) => setSortField(e.target.value as SortField)}
                className="apple-search-input py-2"
              >
                <option value="upload_date">Date</option>
                <option value="name">Name</option>
                <option value="status">Status</option>
              </select>
              
              <button
                onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
                className="p-2 text-apple-ink-48 hover:text-apple-blue hover:bg-apple-parchment rounded-apple-sm transition-colors"
              >
                {sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
              </button>
              
              <div className="flex border border-apple-hairline rounded-apple-sm overflow-hidden">
                <button
                  onClick={() => setViewMode('list')}
                  className={`p-2 ${viewMode === 'list' ? 'bg-apple-blue text-white' : 'text-apple-ink-48 hover:bg-apple-parchment'}`}
                >
                  <List className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`p-2 ${viewMode === 'grid' ? 'bg-apple-blue text-white' : 'text-apple-ink-48 hover:bg-apple-parchment'}`}
                >
                  <Grid className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          {/* Bulk Actions Bar */}
          {isSelectMode && selectedMemories.size > 0 && (
            <div className="flex items-center gap-3 p-3 bg-apple-blue/10 rounded-apple-sm mb-4">
              <span className="text-apple-body-sm text-apple-ink">
                {selectedMemories.size} selected
              </span>
              <button onClick={toggleSelectAll} className="apple-link text-sm">
                {selectedMemories.size === filteredMemories.length ? 'Deselect All' : 'Select All'}
              </button>
              <button 
                onClick={handleBulkRemove}
                className="ml-auto flex items-center gap-2 px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-apple-sm transition-colors"
              >
                <Trash2 className="w-4 h-4" /> Remove
              </button>
            </div>
          )}

          {/* Memories List */}
          <div className="apple-utility-card">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-apple-body-strong text-apple-ink">
                Memories ({filteredMemories.length})
              </h2>
            </div>
            
            {filteredMemories.length > 0 ? (
              viewMode === 'list' ? (
                <div className="space-y-2">
                  {filteredMemories.map((memory) => (
                    <Link key={memory.id} href={`/memories/${memory.id}`}>
                      <div className={`group flex items-center gap-3 p-4 rounded-apple-sm border transition-all ${
                        isSelectMode 
                          ? selectedMemories.has(memory.id) 
                            ? 'border-apple-blue bg-apple-blue/5' 
                            : 'border-apple-hairline hover:border-apple-blue'
                          : 'border-apple-hairline hover:border-apple-blue'
                      }`}>
                        {isSelectMode && (
                          <input
                            type="checkbox"
                            checked={selectedMemories.has(memory.id)}
                            onChange={(e) => { e.preventDefault(); toggleMemorySelection(memory.id); }}
                            className="w-4 h-4 rounded border-apple-hairline text-apple-blue focus:ring-apple-blue"
                          />
                        )}
                        <div className="flex-1 min-w-0">
                          <h3 className="text-apple-body-strong text-apple-ink line-clamp-1 group-hover:text-apple-blue transition-colors">
                            {memory.filename}
                          </h3>
                          <div className="flex items-center gap-2 mt-1">
                            <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                              memory.status === 'processed' ? 'bg-green-100 text-green-800' :
                              memory.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                              'bg-red-100 text-red-800'
                            }`}>
                              {memory.status}
                            </span>
                            <span className="text-apple-caption text-apple-ink-48">
                              {new Date(memory.upload_date).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        {!isSelectMode && (
                          <button 
                            onClick={(e) => { e.preventDefault(); handleRemoveMemory(memory.id); }} 
                            className="p-2 text-apple-ink-48 hover:text-red-600 hover:bg-red-50 rounded-apple-sm transition-colors opacity-0 group-hover:opacity-100"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {filteredMemories.map((memory) => (
                    <Link key={memory.id} href={`/memories/${memory.id}`}>
                      <div className={`group p-4 rounded-apple-sm border transition-all h-full ${
                        isSelectMode 
                          ? selectedMemories.has(memory.id) 
                            ? 'border-apple-blue bg-apple-blue/5' 
                            : 'border-apple-hairline hover:border-apple-blue'
                          : 'border-apple-hairline hover:border-apple-blue'
                      }`}>
                        <div className="flex items-start justify-between mb-2">
                          {isSelectMode && (
                            <input
                              type="checkbox"
                              checked={selectedMemories.has(memory.id)}
                              onChange={(e) => { e.preventDefault(); toggleMemorySelection(memory.id); }}
                              className="w-4 h-4 rounded border-apple-hairline text-apple-blue focus:ring-apple-blue"
                            />
                          )}
                          {!isSelectMode && (
                            <button 
                              onClick={(e) => { e.preventDefault(); handleRemoveMemory(memory.id); }} 
                              className="p-1 text-apple-ink-48 hover:text-red-600 rounded transition-colors opacity-0 group-hover:opacity-100 ml-auto"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                        <h3 className="text-apple-body-strong text-apple-ink line-clamp-2 group-hover:text-apple-blue transition-colors mb-2">
                          {memory.filename}
                        </h3>
                        <div className="flex items-center gap-2 mt-auto">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                            memory.status === 'processed' ? 'bg-green-100 text-green-800' :
                            memory.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {memory.status}
                          </span>
                          <span className="text-apple-caption text-apple-ink-48">
                            {new Date(memory.upload_date).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              )
            ) : (
              <div className="text-center py-12">
                <FileText className="w-12 h-12 text-apple-ink-32 mx-auto mb-4" />
                <p className="text-apple-body text-apple-ink-48 mb-4">
                  {searchQuery ? 'No memories match your search' : 'No memories in this collection yet'}
                </p>
                {!searchQuery && (
                  <button 
                    onClick={() => setShowAddMemories(true)}
                    className="apple-btn-primary inline-flex"
                  >
                    <Plus className="w-4 h-4 mr-2" /> Add Memories
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </section>
    </div>

    {/* Add Memories Modal */}
    {showAddMemories && (
      <AddMemoriesToCollection
        collectionId={collectionId}
        existingMemoryIds={collection?.memories?.map(m => m.id) || []}
        onAdded={() => window.location.reload()}
        onClose={() => setShowAddMemories(false)}
      />
    )}
    </>
  );
}
