/**
 * Add to Collection Component
 * Dropdown to select existing collection or create new one
 */

'use client';

import React, { useState, useEffect, useRef } from 'react';
import { FolderPlus, Check, Search, Plus, Loader2, ChevronDown } from 'lucide-react';
import collectionsService, { Collection } from '@/services/collectionsService';

interface AddToCollectionProps {
  memoryId: number;
  currentCollectionIds?: number[];
  onAdded?: (collection: Collection) => void;
  variant?: 'button' | 'dropdown' | 'icon';
}

const ICON_MAP: Record<string, string> = { 
  folder: '📁', bookmark: '🔖', tag: '🏷️', star: '⭐', heart: '❤️', 
  zap: '⚡', target: '🎯', award: '🏆', book: '📚', code: '💻',
  research: '🔬', certificate: '🎓' 
};

export default function AddToCollection({ 
  memoryId, 
  currentCollectionIds = [], 
  onAdded,
  variant = 'button' 
}: AddToCollectionProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [adding, setAdding] = useState<number | null>(null);
  const [showCreateNew, setShowCreateNew] = useState(false);
  const [newName, setNewName] = useState('');
  const [creating, setCreating] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen) {
      fetchCollections();
    }
  }, [isOpen]);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
        setShowCreateNew(false);
        setSearchQuery('');
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const fetchCollections = async () => {
    try {
      setLoading(true);
      const data = await collectionsService.listCollections();
      setCollections(data);
    } catch (error) {
      console.error('Failed to fetch collections:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCollection = async (collectionId: number) => {
    try {
      setAdding(collectionId);
      await collectionsService.addMemoryToCollection(collectionId, memoryId);
      const collection = collections.find(c => c.id === collectionId);
      if (collection) {
        onAdded?.(collection);
      }
      setIsOpen(false);
      setSearchQuery('');
    } catch (error) {
      console.error('Failed to add to collection:', error);
    } finally {
      setAdding(null);
    }
  };

  const handleCreateAndAdd = async () => {
    if (!newName.trim()) return;
    
    try {
      setCreating(true);
      const newCollection = await collectionsService.createCollection(newName.trim());
      await collectionsService.addMemoryToCollection(newCollection.id, memoryId);
      onAdded?.(newCollection);
      setIsOpen(false);
      setNewName('');
      setShowCreateNew(false);
      setSearchQuery('');
    } catch (error) {
      console.error('Failed to create and add:', error);
    } finally {
      setCreating(false);
    }
  };

  const filteredCollections = collections.filter(c => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const isInCollection = (collectionId: number) => currentCollectionIds.includes(collectionId);

  if (variant === 'icon') {
    return (
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
          title="Add to collection"
        >
          <FolderPlus className="w-5 h-5" />
        </button>
        
        {isOpen && (
          <DropdownContent
            collections={filteredCollections}
            loading={loading}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            showCreateNew={showCreateNew}
            setShowCreateNew={setShowCreateNew}
            newName={newName}
            setNewName={setNewName}
            creating={creating}
            adding={adding}
            isInCollection={isInCollection}
            onAdd={handleAddToCollection}
            onCreateAndAdd={handleCreateAndAdd}
          />
        )}
      </div>
    );
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm font-medium rounded-lg hover:bg-gray-50 transition-colors"
      >
        <FolderPlus className="w-4 h-4" />
        Add to Collection
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {isOpen && (
        <DropdownContent
          collections={filteredCollections}
          loading={loading}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          showCreateNew={showCreateNew}
          setShowCreateNew={setShowCreateNew}
          newName={newName}
          setNewName={setNewName}
          creating={creating}
          adding={adding}
          isInCollection={isInCollection}
          onAdd={handleAddToCollection}
          onCreateAndAdd={handleCreateAndAdd}
        />
      )}
    </div>
  );
}

function DropdownContent({
  collections,
  loading,
  searchQuery,
  setSearchQuery,
  showCreateNew,
  setShowCreateNew,
  newName,
  setNewName,
  creating,
  adding,
  isInCollection,
  onAdd,
  onCreateAndAdd,
}: {
  collections: Collection[];
  loading: boolean;
  searchQuery: string;
  setSearchQuery: (q: string) => void;
  showCreateNew: boolean;
  setShowCreateNew: (show: boolean) => void;
  newName: string;
  setNewName: (n: string) => void;
  creating: boolean;
  adding: number | null;
  isInCollection: (id: number) => boolean;
  onAdd: (id: number) => void;
  onCreateAndAdd: () => void;
}) {
  return (
    <div className="absolute top-full left-0 mt-2 w-80 bg-white rounded-xl shadow-lg border border-gray-200 z-50 overflow-hidden">
      {/* Header */}
      <div className="p-3 border-b border-gray-100">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-semibold text-gray-900">Add to Collection</span>
          {!showCreateNew && (
            <button
              onClick={() => setShowCreateNew(true)}
              className="text-xs text-blue-600 hover:text-blue-700 font-medium"
            >
              + New
            </button>
          )}
        </div>
        
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search collections..."
            className="w-full pl-8 pr-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            autoFocus
          />
        </div>
      </div>

      {/* Create New Form */}
      {showCreateNew && (
        <div className="p-3 bg-blue-50 border-b border-blue-100">
          <label className="text-xs font-medium text-blue-700 mb-1 block">New Collection</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Collection name"
              className="flex-1 px-3 py-1.5 text-sm border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              onKeyDown={(e) => e.key === 'Enter' && onCreateAndAdd()}
              disabled={creating}
            />
            <button
              onClick={onCreateAndAdd}
              disabled={!newName.trim() || creating}
              className="px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Create'}
            </button>
          </div>
        </div>
      )}

      {/* Collections List */}
      <div className="max-h-64 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-center">
            <Loader2 className="w-5 h-5 animate-spin text-gray-400 mx-auto" />
            <span className="text-xs text-gray-500 mt-2 block">Loading...</span>
          </div>
        ) : collections.length === 0 ? (
          <div className="p-4 text-center">
            <span className="text-sm text-gray-500">
              {searchQuery ? 'No collections found' : 'No collections yet'}
            </span>
          </div>
        ) : (
          collections.map((collection) => {
            const inCollection = isInCollection(collection.id);
            const isAdding = adding === collection.id;
            
            return (
              <button
                key={collection.id}
                onClick={() => !inCollection && onAdd(collection.id)}
                disabled={inCollection || isAdding}
                className={`w-full flex items-center gap-3 px-3 py-2.5 text-left hover:bg-gray-50 transition-colors ${
                  inCollection ? 'opacity-60 cursor-default' : 'cursor-pointer'
                }`}
              >
                <span className="text-lg">{ICON_MAP[collection.icon] || '📁'}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-gray-900 truncate">{collection.name}</div>
                  <div className="text-xs text-gray-500">{collection.memory_count} items</div>
                </div>
                {isAdding ? (
                  <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                ) : inCollection ? (
                  <span className="flex items-center gap-1 text-xs text-green-600 font-medium">
                    <Check className="w-4 h-4" /> Added
                  </span>
                ) : (
                  <Plus className="w-4 h-4 text-gray-400" />
                )}
              </button>
            );
          })
        )}
      </div>
    </div>
  );
}
