'use client';

import React, { useState, useCallback, useRef } from 'react';
import { FileText, X, Loader2, CheckCircle2, AlertCircle, UploadCloud } from 'lucide-react';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import memoryService from '@/services/memoryService';

interface UploadItem {
  id: string;
  file: File;
  title: string;
  description: string;
  tags: string;
  status: 'pending' | 'uploading' | 'done' | 'error';
  progress?: number;
  error?: string;
}

export default function UploadPage() {
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const addFiles = useCallback((files: FileList | File[]) => {
    const newItems: UploadItem[] = Array.from(files).map((file) => ({
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      file,
      title: file.name.replace(/\.[^.]+$/, ''),
      description: '',
      tags: '',
      status: 'pending' as const,
    }));
    setUploads((prev) => [...newItems, ...prev]);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length > 0) addFiles(e.dataTransfer.files);
  }, [addFiles]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => setDragging(false), []);

  const updateUpload = (id: string, updates: Partial<UploadItem>) => {
    setUploads((prev) => prev.map((u) => (u.id === id ? { ...u, ...updates } : u)));
  };

  const removeUpload = (id: string) => {
    setUploads((prev) => prev.filter((u) => u.id !== id));
  };

  const uploadItem = async (item: UploadItem) => {
    updateUpload(item.id, { status: 'uploading' });
    try {
      await memoryService.uploadMemory(
        item.file,
        item.title || item.file.name,
        item.description || undefined,
        item.tags || undefined
      );
      updateUpload(item.id, { status: 'done' });
    } catch (err: any) {
      updateUpload(item.id, { status: 'error', error: err?.response?.data?.detail || 'Upload failed' });
    }
  };

  const uploadAll = async () => {
    const pending = uploads.filter((u) => u.status === 'pending');
    await Promise.all(pending.map(uploadItem));
  };

  const pendingCount = uploads.filter((u) => u.status === 'pending').length;
  const uploadingCount = uploads.filter((u) => u.status === 'uploading').length;
  const doneCount = uploads.filter((u) => u.status === 'done').length;

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <ProtectedRoute>
      <div className="-mx-6 -mt-4">
        <section className="bg-white border-b border-gray-200">
          <div className="max-w-[720px] mx-auto text-center py-12 px-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Upload</h1>
            <p className="text-gray-500 mb-8">Add documents, notes, and files to your knowledge base</p>
          </div>
        </section>

        <section className="py-8 px-6">
          <div className="max-w-[720px] mx-auto">
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => inputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
                dragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
              }`}
            >
              <UploadCloud className={`w-12 h-12 mx-auto mb-4 ${dragging ? 'text-blue-500' : 'text-gray-400'}`} />
              <p className="text-gray-700 font-medium mb-1">Drop files here or click to browse</p>
              <p className="text-sm text-gray-400">PDF, TXT, MD, DOCX, and more</p>
              <input
                ref={inputRef}
                type="file"
                multiple
                className="hidden"
                onChange={(e) => { if (e.target.files) addFiles(e.target.files); e.target.value = ''; }}
              />
            </div>

            {uploads.length > 0 && (
              <div className="mt-8">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <h2 className="text-sm font-semibold text-gray-900">{uploads.length} file{uploads.length !== 1 ? 's' : ''}</h2>
                    {doneCount > 0 && <span className="text-xs text-green-600">{doneCount} uploaded</span>}
                    {uploadingCount > 0 && <span className="text-xs text-blue-600">{uploadingCount} uploading…</span>}
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => setUploads([])} className="text-xs text-gray-500 hover:text-gray-700 px-3 py-1.5 rounded-lg hover:bg-gray-100 transition">Clear all</button>
                    {pendingCount > 0 && (
                      <button onClick={uploadAll} className="text-xs font-medium text-white bg-gray-900 hover:bg-gray-800 px-4 py-1.5 rounded-lg transition">
                        Upload {pendingCount} file{pendingCount !== 1 ? 's' : ''}
                      </button>
                    )}
                  </div>
                </div>

                <div className="space-y-3">
                  {uploads.map((item) => (
                    <div key={item.id} className={`p-4 bg-white border rounded-xl transition ${
                      item.status === 'done' ? 'border-green-200 bg-green-50/50' :
                      item.status === 'error' ? 'border-red-200 bg-red-50/50' :
                      'border-gray-200'
                    }`}>
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                          item.status === 'done' ? 'bg-green-100' :
                          item.status === 'error' ? 'bg-red-100' :
                          item.status === 'uploading' ? 'bg-blue-100' :
                          'bg-gray-100'
                        }`}>
                          {item.status === 'done' ? <CheckCircle2 className="w-5 h-5 text-green-600" /> :
                           item.status === 'error' ? <AlertCircle className="w-5 h-5 text-red-600" /> :
                           item.status === 'uploading' ? <Loader2 className="w-5 h-5 text-blue-600 animate-spin" /> :
                           <FileText className="w-5 h-5 text-gray-500" />}
                        </div>
                        <div className="flex-1 min-w-0">
                          {item.status === 'pending' || item.status === 'error' ? (
                            <input
                              type="text"
                              value={item.title}
                              onChange={(e) => updateUpload(item.id, { title: e.target.value })}
                              className="text-sm font-medium text-gray-900 bg-transparent border-b border-gray-200 focus:border-blue-500 focus:outline-none w-full"
                              placeholder="Title"
                            />
                          ) : (
                            <p className="text-sm font-medium text-gray-900 truncate">{item.title}</p>
                          )}
                          <p className="text-xs text-gray-400 mt-0.5">{item.file.name} · {formatSize(item.file.size)}</p>
                          {item.status === 'error' && <p className="text-xs text-red-500 mt-1">{item.error}</p>}
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          {item.status === 'pending' && (
                            <button onClick={() => uploadItem(item)} className="text-xs font-medium text-blue-600 hover:text-blue-700 px-3 py-1.5 rounded-lg hover:bg-blue-50 transition">Upload</button>
                          )}
                          {(item.status === 'pending' || item.status === 'error') && (
                            <button onClick={() => removeUpload(item.id)} className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition">
                              <X className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </div>
                      {item.status === 'pending' && (
                        <div className="mt-3 flex gap-3">
                          <input
                            type="text"
                            value={item.description}
                            onChange={(e) => updateUpload(item.id, { description: e.target.value })}
                            className="text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 flex-1 focus:outline-none focus:border-blue-500"
                            placeholder="Description (optional)"
                          />
                          <input
                            type="text"
                            value={item.tags}
                            onChange={(e) => updateUpload(item.id, { tags: e.target.value })}
                            className="text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-lg px-3 py-1.5 w-40 focus:outline-none focus:border-blue-500"
                            placeholder="Tags (comma sep.)"
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </section>
      </div>
    </ProtectedRoute>
  );
}
