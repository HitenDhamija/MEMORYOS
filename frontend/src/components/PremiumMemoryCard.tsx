/**
 * Premium Memory Card - Apple Design Language
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Calendar, Eye, Trash2, Star } from 'lucide-react';

export interface MemoryCardProps {
  id: string;
  filename: string;
  fileType: string;
  uploadDate: string;
  collections?: Array<{ id: string; name: string }>;
  discoveryCount?: number;
  viewCount?: number;
  status?: 'processing' | 'processed' | 'error';
  preview?: string;
  onDelete?: (id: string) => void;
  onView?: (id: string) => void;
  featured?: boolean;
}

const fileTypeIcons: { [key: string]: string } = {
  pdf: '📄', doc: '📝', docx: '📝', txt: '📋', md: '📄', json: '{}', yaml: '⚙️', code: '💻', image: '🖼️', default: '📦',
};

export const PremiumMemoryCard: React.FC<MemoryCardProps> = ({
  id, filename, fileType, uploadDate, collections = [], discoveryCount = 0, viewCount = 0, status = 'processed', preview, onDelete, onView, featured = false,
}) => {
  const [hovered, setHovered] = useState(false);
  const getFileIcon = () => fileTypeIcons[fileType.toLowerCase()] || fileTypeIcons.default;
  const formatDate = (dateString: string) => new Date(dateString).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

  return (
    <div className="group" onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}>
      <Link href={`/memories/${id}`}>
        <div className={`apple-utility-card relative overflow-hidden cursor-pointer transition-all hover:border-apple-blue ${featured ? 'border-apple-blue' : ''}`}>
          {/* Preview area */}
          <div className="relative h-40 bg-apple-parchment flex items-center justify-center overflow-hidden rounded-apple-sm mb-4">
            {preview ? (
              <img src={preview} alt={filename} className="w-full h-full object-cover" width={400} height={160} loading="lazy" />
            ) : (
              <div className="text-5xl">{getFileIcon()}</div>
            )}
            {featured && (
              <div className="absolute top-3 left-3 bg-apple-ink text-apple-body-dark px-3 py-1 rounded-apple-pill text-apple-fine-print font-semibold flex items-center gap-1">
                <Star size={12} fill="currentColor" /> Featured
              </div>
            )}
            <div className={`absolute top-3 right-3 px-3 py-1 rounded-apple-pill text-apple-fine-print font-semibold ${
              status === 'processing' ? 'bg-apple-parchment text-apple-ink-48' : status === 'error' ? 'bg-red-100 text-red-600' : 'bg-apple-parchment text-apple-ink'
            }`}>
              {status === 'processing' ? 'Processing' : status === 'error' ? 'Error' : 'Processed'}
            </div>
            {hovered && (
              <div className="absolute inset-0 bg-apple-ink/40 backdrop-blur-sm flex items-center justify-center gap-3 animate-fade-in">
                <button onClick={(e) => { e.preventDefault(); onView?.(id); }} className="p-3 bg-white/20 hover:bg-white/30 backdrop-blur-md rounded-full transition-all" aria-label="View memory" title="View">
                  <Eye size={20} className="text-white" />
                </button>
                <button onClick={(e) => { e.preventDefault(); onDelete?.(id); }} className="p-3 bg-white/20 hover:bg-red-500/40 backdrop-blur-md rounded-full transition-all" aria-label="Delete memory" title="Delete">
                  <Trash2 size={20} className="text-white" />
                </button>
              </div>
            )}
          </div>

          {/* Content */}
          <h3 className="text-apple-body-strong text-apple-ink mb-2 line-clamp-2">{filename}</h3>
          <div className="flex items-center gap-2 text-apple-fine-print text-apple-ink-48 mb-3">
            <Calendar size={14} />
            <span>{formatDate(uploadDate)}</span>
            <span>·</span>
            <span className="capitalize">{fileType}</span>
          </div>
          {collections.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-3">
              {collections.slice(0, 2).map((collection) => (
                <span key={collection.id} className="text-apple-fine-print bg-apple-parchment text-apple-ink px-2 py-0.5 rounded-apple-pill">
                  📂 {collection.name}
                </span>
              ))}
              {collections.length > 2 && <span className="text-apple-fine-print text-apple-ink-48">+{collections.length - 2}</span>}
            </div>
          )}
          <div className="flex items-center justify-between text-apple-fine-print text-apple-ink-48 pt-3 border-t border-apple-hairline">
            <div className="flex items-center gap-1"><Eye size={14} /><span>{viewCount} views</span></div>
            <div className="flex items-center gap-1"><span>✨</span><span>{discoveryCount} discoveries</span></div>
          </div>
        </div>
      </Link>
    </div>
  );
};

export const MemoryGrid: React.FC<{
  memories: MemoryCardProps[];
  loading?: boolean;
  onDelete?: (id: string) => void;
  onView?: (id: string) => void;
}> = ({ memories, loading = false, onDelete, onView }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="apple-utility-card animate-pulse h-64" />
        ))}
      </div>
    );
  }
  if (memories.length === 0) {
    return (
      <div className="text-center py-16">
        <div className="text-5xl mb-4">📦</div>
        <h3 className="text-apple-display-md text-apple-ink mb-2">No memories yet</h3>
        <p className="text-apple-body text-apple-ink-48 mb-6">Upload your first memory to get started</p>
        <Link href="/upload" className="apple-btn-primary">Upload Memory</Link>
      </div>
    );
  }
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {memories.map((memory) => (
        <PremiumMemoryCard key={memory.id} {...memory} onDelete={onDelete} onView={onView} />
      ))}
    </div>
  );
};
