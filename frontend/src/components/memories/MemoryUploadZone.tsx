'use client';

import React, { useState, useCallback } from 'react';
import { Upload, AlertCircle } from 'lucide-react';
import memoryService from '@/services/memoryService';

interface MemoryUploadZoneProps {
  onUploadSuccess: () => void;
  onUploadError: (error: string) => void;
}

// Helper function to format file size
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

export default function MemoryUploadZone({
  onUploadSuccess,
  onUploadError,
}: MemoryUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const allowedFileTypes = {
    pdf: 'application/pdf',
    image: 'image/jpeg,image/png,image/gif,image/webp',
    txt: 'text/plain',
    md: 'text/markdown,text/plain',
    bookmark: 'text/plain',
  };

  const validMimeTypes = Object.values(allowedFileTypes)
    .flatMap((types) => types.split(','))
    .filter((type) => type.trim());

  const getFileType = (filename: string): string | null => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const extMap: Record<string, string> = {
      pdf: 'pdf',
      jpg: 'image',
      jpeg: 'image',
      png: 'image',
      gif: 'image',
      webp: 'image',
      txt: 'txt',
      md: 'md',
      markdown: 'md',
      url: 'bookmark',
      webloc: 'bookmark',
    };
    return ext && extMap[ext] ? extMap[ext] : null;
  };

  const validateFile = (file: File): string | null => {
    // Check file type
    const fileType = getFileType(file.name);
    if (!fileType) {
      return `File type not supported. Allowed: PDF, Images (JPG/PNG/GIF/WebP), TXT, Markdown, Bookmarks`;
    }

    // Check file size (100MB)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      return `File too large. Maximum 100MB allowed`;
    }

    return null;
  };

  const handleFile = async (file: File) => {
    const error = validateFile(file);
    if (error) {
      onUploadError(error);
      return;
    }

    setSelectedFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.currentTarget.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !title.trim()) {
      onUploadError('Please select a file and enter a title');
      return;
    }

    setIsUploading(true);
    try {
      await memoryService.uploadMemory(
        selectedFile,
        title.trim(),
        description.trim() || undefined,
        tags.trim() || undefined
      );

      // Reset form
      setSelectedFile(null);
      setTitle('');
      setDescription('');
      setTags('');

      onUploadSuccess();
    } catch (error) {
      onUploadError(
        error instanceof Error ? error.message : 'Upload failed. Please try again.'
      );
    } finally {
      setIsUploading(false);
    }
  };

  const handleCancel = () => {
    setSelectedFile(null);
    setTitle('');
    setDescription('');
    setTags('');
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      {!selectedFile ? (
        // Drop Zone
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`relative rounded-lg border-2 border-dashed p-8 transition-colors ${
            isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-gray-50 hover:border-gray-400'
          }`}
        >
          <div className="flex flex-col items-center justify-center text-center">
            <Upload className="h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              Upload a Memory
            </h3>
            <p className="text-sm text-gray-600 mb-4">
              Drag and drop your file here, or click to select
            </p>
            <p className="text-xs text-gray-500 mb-6">
              Supported: PDF, Images (JPG/PNG/GIF/WebP), TXT, Markdown, Bookmarks
              (Max 100MB)
            </p>

            <label className="inline-block">
              <input
                type="file"
                onChange={handleFileInput}
                accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.txt,.md,.markdown,.url,.webloc"
                className="hidden"
              />
              <span className="inline-block px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer font-medium transition-colors">
                Choose File
              </span>
            </label>
          </div>
        </div>
      ) : (
        // Upload Form
        <div className="rounded-lg border border-gray-300 bg-white p-6">
          <div className="mb-6">
            <h3 className="font-semibold text-gray-900 mb-2">File Selected</h3>
            <p className="text-sm text-gray-600">
              {selectedFile.name}
            </p>
            <p className="text-sm text-gray-500">
              {formatFileSize(selectedFile.size)}
            </p>
          </div>

          <div className="space-y-4">
            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Title <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Give this memory a title..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Add notes about this memory..."
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tags
              </label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="python,tutorial,important (comma-separated)"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Enter tags separated by commas for easy filtering
              </p>
            </div>

            {/* Actions */}
            <div className="flex gap-3 pt-4">
              <button
                onClick={handleUpload}
                disabled={isUploading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed font-medium transition-colors"
              >
                {isUploading ? 'Uploading...' : 'Upload'}
              </button>
              <button
                onClick={handleCancel}
                disabled={isUploading}
                className="flex-1 px-4 py-2 bg-gray-200 text-gray-900 rounded-lg hover:bg-gray-300 disabled:cursor-not-allowed font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
