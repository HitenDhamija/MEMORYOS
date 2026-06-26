/**
 * Collections Grid - Apple Design Language
 * Enhanced with better visual design and hover effects
 */

'use client';

import React from 'react';
import { Trash2, ChevronRight, Pin, Star } from 'lucide-react';
import Link from 'next/link';
import { Collection } from '@/services/collectionsService';

interface CollectionsGridProps {
  collections: Collection[];
  viewMode: 'grid' | 'list';
  onDelete: (collectionId: number) => void;
}

const ICON_MAP: Record<string, string> = { 
  folder: '📁', bookmark: '🔖', tag: '🏷️', star: '⭐', heart: '❤️', 
  zap: '⚡', target: '🎯', award: '🏆', book: '📚', code: '💻',
  research: '🔬', certificate: '🎓' 
};

const COLOR_MAP: Record<string, { bg: string; text: string; border: string }> = {
  blue: { bg: 'bg-blue-50', text: 'text-blue-600', border: 'border-blue-200' },
  red: { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200' },
  green: { bg: 'bg-green-50', text: 'text-green-600', border: 'border-green-200' },
  purple: { bg: 'bg-purple-50', text: 'text-purple-600', border: 'border-purple-200' },
  yellow: { bg: 'bg-yellow-50', text: 'text-yellow-600', border: 'border-yellow-200' },
  pink: { bg: 'bg-pink-50', text: 'text-pink-600', border: 'border-pink-200' },
  indigo: { bg: 'bg-indigo-50', text: 'text-indigo-600', border: 'border-indigo-200' },
  cyan: { bg: 'bg-cyan-50', text: 'text-cyan-600', border: 'border-cyan-200' },
  orange: { bg: 'bg-orange-50', text: 'text-orange-600', border: 'border-orange-200' },
  teal: { bg: 'bg-teal-50', text: 'text-teal-600', border: 'border-teal-200' },
};

export default function CollectionsGrid({ collections, viewMode, onDelete }: CollectionsGridProps) {
  if (viewMode === 'list') {
    return (
      <div className="space-y-2">
        {collections.map((collection) => {
          const colors = COLOR_MAP[collection.color] || COLOR_MAP.blue;
          return (
            <Link key={collection.id} href={`/collections/${collection.id}`}>
              <div className="group flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all cursor-pointer">
                {/* Icon */}
                <div className={`w-12 h-12 rounded-xl ${colors.bg} flex items-center justify-center text-2xl group-hover:scale-110 transition-transform`}>
                  {ICON_MAP[collection.icon] || '📁'}
                </div>
                
                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                      {collection.name}
                    </h3>
                    {collection.is_pinned && <Pin className="w-3.5 h-3.5 text-blue-500" />}
                    {collection.is_favorite && <Star className="w-3.5 h-3.5 text-yellow-500 fill-yellow-500" />}
                  </div>
                  {collection.description && (
                    <p className="text-xs text-gray-500 truncate mt-0.5">{collection.description}</p>
                  )}
                </div>
                
                {/* Meta */}
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-full">
                    {collection.memory_count} {collection.memory_count === 1 ? 'item' : 'items'}
                  </span>
                  <button
                    onClick={(e) => { e.preventDefault(); e.stopPropagation(); if (confirm(`Delete "${collection.name}"?`)) onDelete(collection.id); }}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                    aria-label={`Delete ${collection.name}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors" />
                </div>
              </div>
            </Link>
          );
        })}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {collections.map((collection) => {
        const colors = COLOR_MAP[collection.color] || COLOR_MAP.blue;
        return (
          <Link key={collection.id} href={`/collections/${collection.id}`}>
            <div className="group bg-white rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-lg transition-all cursor-pointer h-full flex flex-col overflow-hidden">
              {/* Header with icon */}
              <div className={`relative h-28 ${colors.bg} flex items-center justify-center`}>
                <span className="text-5xl group-hover:scale-110 transition-transform duration-300">
                  {ICON_MAP[collection.icon] || '📁'}
                </span>
                
                {/* Badges */}
                <div className="absolute top-2 right-2 flex gap-1">
                  {collection.is_pinned && (
                    <span className="p-1 bg-white/90 rounded-full shadow-sm">
                      <Pin className="w-3.5 h-3.5 text-blue-500" />
                    </span>
                  )}
                  {collection.is_favorite && (
                    <span className="p-1 bg-white/90 rounded-full shadow-sm">
                      <Star className="w-3.5 h-3.5 text-yellow-500 fill-yellow-500" />
                    </span>
                  )}
                </div>
                
                {/* Delete button */}
                <button
                  onClick={(e) => { e.preventDefault(); e.stopPropagation(); if (confirm(`Delete "${collection.name}"?`)) onDelete(collection.id); }}
                  className="absolute top-2 left-2 p-1.5 bg-white/90 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-full shadow-sm transition-all opacity-0 group-hover:opacity-100"
                  aria-label={`Delete ${collection.name}`}
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
              
              {/* Content */}
              <div className="p-4 flex-1 flex flex-col">
                <h3 className="text-sm font-semibold text-gray-900 line-clamp-1 group-hover:text-blue-600 transition-colors mb-1">
                  {collection.name}
                </h3>
                {collection.description && (
                  <p className="text-xs text-gray-500 line-clamp-2 mb-3 flex-1">{collection.description}</p>
                )}
                
                {/* Footer */}
                <div className="flex items-center justify-between pt-3 border-t border-gray-100 mt-auto">
                  <span className="text-xs font-medium text-gray-500">
                    {collection.memory_count} {collection.memory_count === 1 ? 'memory' : 'memories'}
                  </span>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colors.bg} ${colors.text}`}>
                    {collection.color}
                  </span>
                </div>
              </div>
            </div>
          </Link>
        );
      })}
    </div>
  );
}
