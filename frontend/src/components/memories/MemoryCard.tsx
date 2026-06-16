'use client';

import React, { useState } from 'react';
import { Download, Trash2, Edit2 } from 'lucide-react';
import memoryService, { Memory } from '@/services/memoryService';

interface MemoryCardProps {
  memory: Memory;
  onDelete: () => void;
  onUpdate: () => void;
}

// Helper functions for display formatting
const getFileIcon = (fileType: string): string => {
  const icons: Record<string, string> = {
    pdf: '📄',
    image: '🖼️',
    txt: '📝',
    md: '📋',
    bookmark: '🔖',
    other: '📎',
  };
  return icons[fileType] || icons.other;
};

const getStatusColor = (status: string): string => {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800',
    uploaded: 'bg-blue-100 text-blue-800',
    processing: 'bg-purple-100 text-purple-800',
    processed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };
  return colors[status] || colors.pending;
};

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

export default function MemoryCard({ memory, onDelete, onUpdate }: MemoryCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [editTitle, setEditTitle] = useState(memory.title);
  const [editDescription, setEditDescription] = useState(memory.description || '');
  const [editTags, setEditTags] = useState(
    Array.isArray(memory.tags) ? memory.tags.join(',') : memory.tags || ''
  );
  const [isSaving, setIsSaving] = useState(false);

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this memory?')) return;

    setIsDeleting(true);
    try {
      await memoryService.deleteMemory(memory.id);
      onDelete();
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to delete memory');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleSaveEdit = async () => {
    setIsSaving(true);
    try {
      await memoryService.updateMemory(memory.id, {
        title: editTitle,
        description: editDescription || undefined,
        tags: editTags || undefined,
      });
      setShowEditForm(false);
      onUpdate();
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to update memory');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDownload = async () => {
    try {
      await memoryService.downloadMemory(memory.id, memory.original_filename);
    } catch (error) {
      alert(error instanceof Error ? error.message : 'Failed to download file');
    }
  };

  const fileIcon = getFileIcon(memory.file_type);
  const statusColor = getStatusColor(memory.processing_status);
  const formattedDate = formatDate(memory.upload_date);
  const fileSize = formatFileSize(memory.file_size);

  if (showEditForm) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <h3 className="font-semibold text-gray-900 mb-3">Edit Memory</h3>

        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title
            </label>
            <input
              type="text"
              value={editTitle}
              onChange={(e) => setEditTitle(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={editDescription}
              onChange={(e) => setEditDescription(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Tags
            </label>
            <input
              type="text"
              value={editTags}
              onChange={(e) => setEditTags(e.target.value)}
              placeholder="python,tutorial"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex gap-2 pt-2">
            <button
              onClick={handleSaveEdit}
              disabled={isSaving}
              className="flex-1 px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium transition-colors"
            >
              {isSaving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={() => setShowEditForm(false)}
              className="flex-1 px-3 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {/* Header */}
      <div className="p-4">
        <div className="flex items-start gap-3 mb-3">
          <span className="text-3xl flex-shrink-0">{fileIcon}</span>
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 break-words line-clamp-2">
              {memory.title}
            </h3>
            <p className="text-xs text-gray-500 mt-1">
              {memory.original_filename} · {fileSize}
            </p>
          </div>
        </div>

        {/* Type Badge */}
        <div className="flex items-center gap-2 mb-3">
          <span className="inline-block px-2 py-1 text-xs font-medium bg-gray-100 text-gray-800 rounded">
            {memory.file_type}
          </span>
          <span className={`inline-block px-2 py-1 text-xs font-medium rounded ${statusColor}`}>
            {memory.processing_status}
          </span>
        </div>

        {/* Description */}
        {memory.description && (
          <p className="text-sm text-gray-600 mb-3 line-clamp-2">
            {memory.description}
          </p>
        )}

        {/* Tags */}
        {memory.tags && (
          <div className="flex flex-wrap gap-1 mb-3">
            {(Array.isArray(memory.tags)
              ? memory.tags
              : String(memory.tags)
                  .split(',')
                  .filter((t) => t.trim())
            ).map((tag, idx) => (
              <span
                key={idx}
                className="inline-block px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded"
              >
                #{tag.trim()}
              </span>
            ))}
          </div>
        )}

        {/* Metadata */}
        <div className="text-xs text-gray-500 mb-4">
          Uploaded {formattedDate}
        </div>
      </div>

      {/* Actions */}
      <div className="border-t border-gray-200 px-4 py-3 bg-gray-50 flex gap-2">
        <button
          onClick={handleDownload}
          title="Download file"
          className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
        >
          <Download className="h-4 w-4" />
          <span className="hidden sm:inline">Download</span>
        </button>

        <button
          onClick={() => setShowEditForm(true)}
          title="Edit metadata"
          className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors"
        >
          <Edit2 className="h-4 w-4" />
          <span className="hidden sm:inline">Edit</span>
        </button>

        <button
          onClick={handleDelete}
          disabled={isDeleting}
          title="Delete memory"
          className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm text-red-700 bg-white border border-gray-300 rounded hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Trash2 className="h-4 w-4" />
          <span className="hidden sm:inline">Delete</span>
        </button>
      </div>
    </div>
  );
}
