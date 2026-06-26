/**
 * Memory Card - Apple Design Language
 */

'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { Download, Trash2, Edit2 } from 'lucide-react';
import memoryService, { Memory } from '@/services/memoryService';

interface MemoryCardProps {
  memory: Memory;
  onDelete: () => void;
  onUpdate: () => void;
}

const getFileIcon = (fileType: string): string => {
  const icons: Record<string, string> = { pdf: '📄', image: '🖼️', txt: '📝', md: '📋', bookmark: '🔖', other: '📎' };
  return icons[fileType] || icons.other;
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

const formatDate = (dateString: string): string => new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

export default function MemoryCard({ memory, onDelete, onUpdate }: MemoryCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editTitle, setEditTitle] = useState(memory.title);
  const [editDescription, setEditDescription] = useState(memory.description || '');
  const [editTags, setEditTags] = useState(Array.isArray(memory.tags) ? memory.tags.join(',') : memory.tags || '');
  const [isSaving, setIsSaving] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this memory?')) return;
    setIsDeleting(true);
    try { await memoryService.deleteMemory(memory.id); onDelete(); } catch (error) { alert(error instanceof Error ? error.message : 'Failed to delete'); } finally { setIsDeleting(false); }
  };

  const handleSaveEdit = async () => {
    setIsSaving(true);
    try { await memoryService.updateMemory(memory.id, { title: editTitle, description: editDescription || undefined, tags: editTags || undefined }); setShowEditForm(false); onUpdate(); } catch (error) { alert(error instanceof Error ? error.message : 'Failed to update'); } finally { setIsSaving(false); }
  };

  const handleDownload = async () => {
    try { await memoryService.downloadMemory(memory.id, memory.original_filename); } catch (error) { alert(error instanceof Error ? error.message : 'Failed to download'); }
  };

  if (showEditForm) {
    return (
      <div className="apple-utility-card">
        <h3 className="text-apple-body-strong text-apple-ink mb-3">Edit Memory</h3>
        <div className="space-y-3">
          <div>
            <label className="block text-apple-caption-strong text-apple-ink mb-1">Title</label>
            <input type="text" name="edit-title" autoComplete="off" value={editTitle} onChange={(e) => setEditTitle(e.target.value)} className="apple-search-input" />
          </div>
          <div>
            <label className="block text-apple-caption-strong text-apple-ink mb-1">Description</label>
            <textarea name="edit-description" value={editDescription} onChange={(e) => setEditDescription(e.target.value)} rows={2} className="apple-search-input h-auto min-h-[60px] resize-y" />
          </div>
          <div>
            <label className="block text-apple-caption-strong text-apple-ink mb-1">Tags</label>
            <input type="text" name="edit-tags" autoComplete="off" value={editTags} onChange={(e) => setEditTags(e.target.value)} placeholder="python,tutorial" className="apple-search-input" />
          </div>
          <div className="flex gap-2 pt-2">
            <button onClick={handleSaveEdit} disabled={isSaving} className="apple-btn-primary flex-1 disabled:opacity-50">{isSaving ? 'Saving…' : 'Save'}</button>
            <button onClick={() => setShowEditForm(false)} className="apple-btn-secondary flex-1">Cancel</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="apple-utility-card flex flex-col h-full !p-0">
      <Link href={`/memories/${memory.id}`} className="block flex-1">
        <div className="px-6 pt-6 pb-5 hover:bg-apple-parchment transition-colors h-full">
          <div className="flex items-start gap-4 mb-4">
            <span className="text-4xl flex-shrink-0">{getFileIcon(memory.file_type)}</span>
            <div className="flex-1 min-w-0">
              <h3 className="text-apple-body-strong text-apple-ink break-words line-clamp-2 hover:text-apple-blue transition-colors">{memory.title}</h3>
              <p className="text-apple-fine-print text-apple-ink-48 mt-1.5">{memory.original_filename} · {formatFileSize(memory.file_size)}</p>
            </div>
          </div>
          <div className="flex items-center gap-2 mb-4">
            <span className="inline-block px-2.5 py-1 text-apple-fine-print bg-apple-parchment text-apple-ink rounded-apple-pill">{memory.file_type}</span>
            <span className="inline-block px-2.5 py-1 text-apple-fine-print bg-apple-parchment text-apple-ink rounded-apple-pill capitalize">{memory.processing_status}</span>
          </div>
          {memory.description && <p className="text-apple-caption text-apple-ink-48 mb-4 line-clamp-2">{memory.description}</p>}
          {memory.tags && (
            <div className="flex flex-wrap gap-1.5 mb-4">
              {(Array.isArray(memory.tags) ? memory.tags : String(memory.tags).split(',').filter((t) => t.trim())).map((tag, idx) => (
                <span key={idx} className="inline-block px-2.5 py-1 text-apple-fine-print bg-apple-blue/10 text-apple-blue rounded-apple-pill">#{tag.trim()}</span>
              ))}
            </div>
          )}
          <div className="text-apple-fine-print text-apple-ink-48">Uploaded {formatDate(memory.upload_date)}</div>
        </div>
      </Link>
      <div className="border-t border-apple-hairline px-6 py-4 flex gap-3">
        <button onClick={(e) => { e.preventDefault(); handleDownload(); }} aria-label="Download file" className="flex-1 inline-flex items-center justify-center px-3 py-2.5 text-sm rounded-apple-pill border border-apple-blue text-apple-blue hover:bg-apple-blue/5 transition-all min-w-0">
          <Download className="h-4 w-4" />
        </button>
        <button onClick={() => setShowEditForm(true)} aria-label="Edit metadata" className="flex-1 inline-flex items-center justify-center px-3 py-2.5 text-sm rounded-apple-pill border border-apple-blue text-apple-blue hover:bg-apple-blue/5 transition-all min-w-0">
          <Edit2 className="h-4 w-4" />
        </button>
        <button onClick={handleDelete} disabled={isDeleting} aria-label="Delete memory" className="flex-1 inline-flex items-center justify-center px-3 py-2.5 text-sm rounded-apple-pill border border-red-300 text-red-600 hover:bg-red-50 transition-all disabled:opacity-50 min-w-0">
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
