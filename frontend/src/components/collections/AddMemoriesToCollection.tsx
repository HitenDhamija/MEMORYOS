/**
 * Add Memories to Collection Component
 * Modal to search and select existing memories to add to a collection
 */

'use client';

import React, { useState, useEffect } from 'react';
import { Search, X, Check, Loader2, FileText, Calendar, Tag } from 'lucide-react';
import collectionsService from '@/services/collectionsService';
import apiClient from '@/services/apiClient';

interface Memory {
  id: number;
  title: string;
  original_filename: string;
  file_type: string;
  upload_date: string;
  tags?: string[];
  summary?: string;
}

interface AddMemoriesToCollectionProps {
  collectionId: number;
  existingMemoryIds: number[];
  onAdded?: (memoryIds: number[]) => void;
  onClose?: () => void;
}

const FILE_TYPE_ICONS: Record<string, string> = {
  pdf: '📄',
  doc: '📝',
  docx: '📝',
  txt: '📄',
  md: '📝',
  jpg: '🖼️',
  jpeg: '🖼️',
  png: '🖼️',
  ppt: '📊',
  pptx: '📊',
  xls: '📊',
  xlsx: '📊',
};

export default function AddMemoriesToCollection({
  collectionId,
  existingMemoryIds,
  onAdded,
  onClose,
}: AddMemoriesToCollectionProps) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [adding, setAdding] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchMemories();
  }, []);

  const fetchMemories = async () => {
    try {
      setLoading(true);
      const response = await apiClient.get('/v1/memories', { params: { limit: 100 } });
      setMemories(response.data.items || []);
    } catch (err) {
      console.error('Failed to fetch memories:', err);
      setError('Failed to load memories');
    } finally {
      setLoading(false);
    }
  };

  const filteredMemories = memories.filter(m => {
    const matchesSearch = m.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.original_filename.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.tags?.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesSearch;
  });

  const toggleSelect = (memoryId: number) => {
    if (existingMemoryIds.includes(memoryId)) return;
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(memoryId)) {
        next.delete(memoryId);
      } else {
        next.add(memoryId);
      }
      return next;
    });
  };

  const handleAdd = async () => {
    if (selectedIds.size === 0) return;

    try {
      setAdding(true);
      setError('');
      
      const promises = Array.from(selectedIds).map(memoryId =>
        collectionsService.addMemoryToCollection(collectionId, memoryId)
      );
      
      await Promise.all(promises);
      onAdded?.(Array.from(selectedIds));
      onClose?.();
    } catch (err) {
      console.error('Failed to add memories:', err);
      setError('Failed to add some memories');
    } finally {
      setAdding(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div 
        className="bg-white rounded-2xl w-full max-w-2xl max-h-[80vh] flex flex-col shadow-2xl"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Add Memories to Collection</h2>
            <p className="text-sm text-gray-500 mt-0.5">Select existing memories to add</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Search */}
        <div className="p-4 border-b border-gray-100">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by title, filename, or tags..."
              className="w-full pl-10 pr-4 py-2.5 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              autoFocus
            />
          </div>
        </div>

        {/* Memories List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
              <span className="ml-2 text-gray-500">Loading memories...</span>
            </div>
          ) : filteredMemories.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500">
                {searchQuery ? 'No memories found matching your search' : 'No memories available'}
              </p>
            </div>
          ) : (
            <div className="divide-y divide-gray-50">
              {filteredMemories.map(memory => {
                const isExisting = existingMemoryIds.includes(memory.id);
                const isSelected = selectedIds.has(memory.id);

                return (
                  <button
                    key={memory.id}
                    onClick={() => toggleSelect(memory.id)}
                    disabled={isExisting}
                    className={`w-full flex items-center gap-3 p-3 text-left transition-colors ${
                      isExisting
                        ? 'opacity-50 cursor-not-allowed bg-gray-50'
                        : isSelected
                          ? 'bg-blue-50'
                          : 'hover:bg-gray-50'
                    }`}
                  >
                    {/* Checkbox */}
                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                      isExisting
                        ? 'border-gray-300 bg-gray-100'
                        : isSelected
                          ? 'border-blue-500 bg-blue-500'
                          : 'border-gray-300'
                    }`}>
                      {isExisting ? (
                        <Check className="w-3 h-3 text-gray-400" />
                      ) : isSelected ? (
                        <Check className="w-3 h-3 text-white" />
                      ) : null}
                    </div>

                    {/* Icon */}
                    <span className="text-2xl">
                      {FILE_TYPE_ICONS[memory.file_type] || '📄'}
                    </span>

                    {/* Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium text-gray-900 truncate">
                        {memory.title || memory.original_filename}
                      </h3>
                      <div className="flex items-center gap-3 mt-0.5">
                        <span className="text-xs text-gray-500 flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {new Date(memory.upload_date).toLocaleDateString()}
                        </span>
                        {memory.tags && memory.tags.length > 0 && (
                          <span className="text-xs text-gray-500 flex items-center gap-1">
                            <Tag className="w-3 h-3" />
                            {memory.tags.slice(0, 2).join(', ')}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Status */}
                    {isExisting && (
                      <span className="text-xs text-gray-500 font-medium">Already added</span>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        {error && (
          <div className="px-4 py-2 bg-red-50 border-t border-red-100">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
        <div className="flex items-center justify-between p-4 border-t border-gray-100">
          <span className="text-sm text-gray-500">
            {selectedIds.size} {selectedIds.size === 1 ? 'memory' : 'memories'} selected
          </span>
          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleAdd}
              disabled={selectedIds.size === 0 || adding}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {adding ? (
                <span className="flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Adding...
                </span>
              ) : (
                `Add ${selectedIds.size > 0 ? selectedIds.size : ''} ${selectedIds.size === 1 ? 'Memory' : 'Memories'}`
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
