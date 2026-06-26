/**
 * Premium Collection Card Component
 * 
 * Beautiful collection cards with statistics, progress bars, and
 * visual indicators.
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Folder, MoreVertical, Edit, Trash2, Share2, Plus, ChevronRight } from 'lucide-react';

export interface CollectionCardProps {
  id: string;
  name: string;
  description?: string;
  memoryCount: number;
  maxMemories?: number;
  color?: 'blue' | 'purple' | 'green' | 'orange' | 'pink' | 'red';
  createdAt: string;
  lastUpdated?: string;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onShare?: (id: string) => void;
}

const colorGradients: { [key: string]: string } = {
  blue: 'from-blue-500 to-blue-600',
  purple: 'from-purple-500 to-purple-600',
  green: 'from-green-500 to-green-600',
  orange: 'from-orange-500 to-orange-600',
  pink: 'from-pink-500 to-pink-600',
  red: 'from-red-500 to-red-600',
};

const colorLight: { [key: string]: string } = {
  blue: 'bg-blue-50 dark:bg-blue-950/30 border-blue-200 dark:border-blue-800',
  purple: 'bg-purple-50 dark:bg-purple-950/30 border-purple-200 dark:border-purple-800',
  green: 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-800',
  orange: 'bg-orange-50 dark:bg-orange-950/30 border-orange-200 dark:border-orange-800',
  pink: 'bg-pink-50 dark:bg-pink-950/30 border-pink-200 dark:border-pink-800',
  red: 'bg-red-50 dark:bg-red-950/30 border-red-200 dark:border-red-800',
};

export const PremiumCollectionCard: React.FC<CollectionCardProps> = ({
  id,
  name,
  description,
  memoryCount,
  maxMemories = 100,
  color = 'blue',
  createdAt,
  lastUpdated,
  onEdit,
  onDelete,
  onShare,
}) => {
  const [hovered, setHovered] = useState(false);
  const [showMenu, setShowMenu] = useState(false);

  const progressPercent = (memoryCount / maxMemories) * 100;

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div
      className="group"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <Link href={`/collections/${id}`}>
        <div className={`
          relative rounded-2xl border overflow-hidden shadow-md hover:shadow-xl
          transition-all duration-300 transform hover:scale-105 cursor-pointer
          ${colorLight[color]}
        `}>
          {/* Header with gradient */}
          <div className={`bg-gradient-to-r ${colorGradients[color]} p-6 text-white relative overflow-hidden`}>
            {/* Background animation */}
            <div className="absolute inset-0 opacity-20">
              <div className="absolute top-0 right-0 w-32 h-32 bg-white rounded-full blur-2xl -mr-16 -mt-16" />
            </div>

            <div className="relative flex items-start justify-between mb-4">
              <div className="p-3 bg-white/20 backdrop-blur-sm rounded-lg">
                <Folder size={28} />
              </div>
              {hovered && (
                <div className="relative">
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      setShowMenu(!showMenu);
                    }}
                    className="p-2 hover:bg-white/20 rounded-lg transition"
                    aria-label="More options"
                    aria-expanded={showMenu}
                  >
                    <MoreVertical size={18} />
                  </button>
                  {showMenu && (
                    <div className="absolute right-0 top-full mt-2 bg-white dark:bg-gray-800 rounded-lg shadow-lg z-50 w-44 overflow-hidden">
                      {onEdit && (
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            onEdit(id);
                            setShowMenu(false);
                          }}
                          className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white flex items-center gap-2"
                        >
                          <Edit size={16} /> Edit
                        </button>
                      )}
                      {onShare && (
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            onShare(id);
                            setShowMenu(false);
                          }}
                          className="w-full text-left px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-900 dark:text-white flex items-center gap-2"
                        >
                          <Share2 size={16} /> Share
                        </button>
                      )}
                      {onDelete && (
                        <button
                          onClick={(e) => {
                            e.preventDefault();
                            onDelete(id);
                            setShowMenu(false);
                          }}
                          className="w-full text-left px-4 py-2 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 flex items-center gap-2 border-t border-gray-200 dark:border-gray-700"
                        >
                          <Trash2 size={16} /> Delete
                        </button>
                      )}
                    </div>
                  )}
                </div>
              )}
            </div>

            <h3 className="text-2xl font-bold mb-1">{name}</h3>
            {description && <p className="text-white/80 text-sm line-clamp-1">{description}</p>}
          </div>

          {/* Content area */}
          <div className="p-6">
            {/* Memory count */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                  Memories
                </span>
                <span className="text-sm font-bold text-gray-900 dark:text-white">
                  {memoryCount} / {maxMemories}
                </span>
              </div>
              {/* Progress bar */}
              <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full bg-gradient-to-r ${colorGradients[color]} transition-all duration-500`}
                  style={{ width: `${Math.min(progressPercent, 100)}%` }}
                />
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4 mb-4 py-4 border-y border-gray-200 dark:border-gray-700">
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {Math.round(progressPercent)}%
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Filled</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-gray-900 dark:text-white">
                  {maxMemories - memoryCount}
                </p>
                <p className="text-xs text-gray-600 dark:text-gray-400">Available</p>
              </div>
            </div>

            {/* Dates */}
            <div className="space-y-2 text-xs text-gray-600 dark:text-gray-400 mb-4">
              <p>Created: {formatDate(createdAt)}</p>
              {lastUpdated && <p>Updated: {formatDate(lastUpdated)}</p>}
            </div>

            {/* View button */}
            <button className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition flex items-center justify-center gap-2">
              View Collection <ChevronRight size={16} />
            </button>
          </div>

          {/* Bottom accent */}
          <div className={`absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r ${colorGradients[color]} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
        </div>
      </Link>
    </div>
  );
};

/**
 * Collections Grid Component
 */
export const CollectionsGrid: React.FC<{
  collections: CollectionCardProps[];
  loading?: boolean;
  onEdit?: (id: string) => void;
  onDelete?: (id: string) => void;
  onShare?: (id: string) => void;
}> = ({ collections, loading = false, onEdit, onDelete, onShare }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="rounded-2xl bg-gray-200 dark:bg-gray-700 animate-pulse h-80" />
        ))}
      </div>
    );
  }

  if (collections.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-6xl mb-4">📂</div>
        <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">No collections yet</h3>
        <p className="text-gray-600 dark:text-gray-400 mb-6">Create your first collection to organize memories</p>
        <Link
          href="/collections/new"
          className="inline-block px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition flex items-center gap-2"
        >
          <Plus size={20} /> Create Collection
        </Link>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {collections.map((collection) => (
        <PremiumCollectionCard
          key={collection.id}
          {...collection}
          onEdit={onEdit}
          onDelete={onDelete}
          onShare={onShare}
        />
      ))}
    </div>
  );
};
