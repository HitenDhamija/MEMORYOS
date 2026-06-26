/**
 * Memory Upload Zone - Apple Design Language
 */

'use client';

import React, { useState } from 'react';
import { Upload } from 'lucide-react';
import memoryService from '@/services/memoryService';

interface MemoryUploadZoneProps {
  onUploadSuccess: () => void;
  onUploadError: (error: string) => void;
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
};

export default function MemoryUploadZone({ onUploadSuccess, onUploadError }: MemoryUploadZoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [tags, setTags] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const getFileType = (filename: string): string | null => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const extMap: Record<string, string> = { pdf: 'pdf', jpg: 'image', jpeg: 'image', png: 'image', gif: 'image', webp: 'image', txt: 'txt', md: 'md', markdown: 'md', docx: 'docx', url: 'bookmark', webloc: 'bookmark' };
    return ext && extMap[ext] ? extMap[ext] : null;
  };

  const validateFile = (file: File): string | null => {
    const fileType = getFileType(file.name);
    if (!fileType) return 'File type not supported. Allowed: PDF, DOCX, Images, TXT, Markdown, Bookmarks';
    if (file.size > 100 * 1024 * 1024) return 'File too large. Maximum 100MB allowed';
    return null;
  };

  const handleFile = async (file: File) => {
    const error = validateFile(file);
    if (error) { onUploadError(error); return; }
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile || !title.trim()) { onUploadError('Please select a file and enter a title'); return; }
    setIsUploading(true);
    try {
      await memoryService.uploadMemory(selectedFile, title.trim(), description.trim() || undefined, tags.trim() || undefined);
      setSelectedFile(null); setTitle(''); setDescription(''); setTags('');
      onUploadSuccess();
    } catch (error) { onUploadError(error instanceof Error ? error.message : 'Upload failed.'); } finally { setIsUploading(false); }
  };

  if (!selectedFile) {
    return (
      <div onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }} onDragLeave={(e) => { e.preventDefault(); setIsDragging(false); }} onDrop={(e) => { e.preventDefault(); setIsDragging(false); if (e.dataTransfer.files.length > 0) handleFile(e.dataTransfer.files[0]); }} className={`relative rounded-apple-lg border-2 border-dashed p-8 transition-colors ${isDragging ? 'border-apple-blue bg-apple-blue/5' : 'border-apple-hairline hover:border-apple-blue/40'}`}>
        <div className="flex flex-col items-center justify-center text-center">
          <Upload className="h-12 w-12 text-apple-ink-48 mb-4" />
          <h3 className="text-apple-body-strong text-apple-ink mb-2">Upload a Memory</h3>
          <p className="text-apple-caption text-apple-ink-48 mb-4">Drag and drop your file here, or click to select</p>
          <p className="text-apple-fine-print text-apple-ink-48 mb-6">PDF, DOCX, Images, TXT, Markdown, Bookmarks · Max 100MB</p>
          <label className="inline-block">
            <input type="file" name="memory-file" aria-label="Upload memory file" onChange={(e) => { if (e.currentTarget.files && e.currentTarget.files.length > 0) handleFile(e.currentTarget.files[0]); }} accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.txt,.md,.markdown,.docx,.url,.webloc" className="hidden" />
            <span className="apple-btn-primary cursor-pointer">Choose File</span>
          </label>
        </div>
      </div>
    );
  }

  return (
    <div className="apple-utility-card">
      <div className="mb-6">
        <h3 className="text-apple-body-strong text-apple-ink mb-1">File Selected</h3>
        <p className="text-apple-caption text-apple-ink">{selectedFile.name}</p>
        <p className="text-apple-fine-print text-apple-ink-48">{formatFileSize(selectedFile.size)}</p>
      </div>
      <div className="space-y-4">
        <div>
          <label className="block text-apple-caption-strong text-apple-ink mb-1">Title <span className="text-red-500">*</span></label>
          <input type="text" name="memory-title" autoComplete="off" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Give this memory a title…" className="apple-search-input" />
        </div>
        <div>
          <label className="block text-apple-caption-strong text-apple-ink mb-1">Description</label>
          <textarea name="memory-description" value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Add notes about this memory…" rows={3} className="apple-search-input h-auto min-h-[80px] resize-y" />
        </div>
        <div>
          <label className="block text-apple-caption-strong text-apple-ink mb-1">Tags</label>
          <input type="text" name="memory-tags" autoComplete="off" value={tags} onChange={(e) => setTags(e.target.value)} placeholder="python,tutorial,important" className="apple-search-input" />
          <p className="text-apple-fine-print text-apple-ink-48 mt-1">Comma-separated</p>
        </div>
        <div className="flex gap-3 pt-4">
          <button onClick={handleUpload} disabled={isUploading} className="apple-btn-primary flex-1 disabled:opacity-50">{isUploading ? 'Uploading…' : 'Upload'}</button>
          <button onClick={() => { setSelectedFile(null); setTitle(''); setDescription(''); setTags(''); }} disabled={isUploading} className="apple-btn-secondary flex-1 disabled:opacity-50">Cancel</button>
        </div>
      </div>
    </div>
  );
}
