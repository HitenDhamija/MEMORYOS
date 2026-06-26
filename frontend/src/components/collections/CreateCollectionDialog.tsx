/**
 * Create Collection Dialog - Apple Design Language
 * Enhanced with better UI, error handling, and validation
 */

'use client';

import React, { useState } from 'react';
import { X, Loader2, Check } from 'lucide-react';

interface CreateCollectionDialogProps {
  open: boolean;
  onClose: () => void;
  onCreate: (name: string, description?: string, color?: string, icon?: string) => Promise<void>;
}

const COLORS = [
  { name: 'blue', hex: '#007AFF' },
  { name: 'red', hex: '#FF3B30' },
  { name: 'green', hex: '#34C759' },
  { name: 'purple', hex: '#AF52DE' },
  { name: 'yellow', hex: '#FFCC00' },
  { name: 'pink', hex: '#FF2D55' },
  { name: 'indigo', hex: '#5856D6' },
  { name: 'cyan', hex: '#5AC8FA' },
  { name: 'orange', hex: '#FF9500' },
  { name: 'teal', hex: '#30B0C7' },
];

const ICONS = [
  { name: 'folder', emoji: '📁' },
  { name: 'bookmark', emoji: '🔖' },
  { name: 'tag', emoji: '🏷️' },
  { name: 'star', emoji: '⭐' },
  { name: 'heart', emoji: '❤️' },
  { name: 'zap', emoji: '⚡' },
  { name: 'target', emoji: '🎯' },
  { name: 'award', emoji: '🏆' },
  { name: 'book', emoji: '📚' },
  { name: 'code', emoji: '💻' },
  { name: 'research', emoji: '🔬' },
  { name: 'certificate', emoji: '🎓' },
];

export default function CreateCollectionDialog({ open, onClose, onCreate }: CreateCollectionDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [color, setColor] = useState('blue');
  const [icon, setIcon] = useState('folder');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!name.trim()) {
      setError('Collection name is required');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      await onCreate(name.trim(), description.trim() || undefined, color, icon);
      // Reset form on success
      setName('');
      setDescription('');
      setColor('blue');
      setIcon('folder');
      onClose();
    } catch (err: any) {
      const message = err?.response?.data?.detail || err?.message || 'Failed to create collection';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setError(null);
      onClose();
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={handleClose}
      />
      
      {/* Dialog */}
      <div className="relative w-full max-w-md mx-4 bg-white rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-2">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Create New Collection</h2>
            <p className="text-sm text-gray-500 mt-1">Organize your memories into a new collection</p>
          </div>
          <button
            onClick={handleClose}
            disabled={loading}
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-full transition-colors disabled:opacity-50"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-4 space-y-5">
          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {error}
            </div>
          )}

          {/* Collection Name */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Collection Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => { setName(e.target.value); setError(null); }}
              placeholder="e.g., Backend Development"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400"
              disabled={loading}
              autoFocus
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Description <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Add a description"
              rows={2}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400 resize-none"
              disabled={loading}
            />
          </div>

          {/* Color Picker */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Color</label>
            <div className="flex gap-2 flex-wrap">
              {COLORS.map((c) => (
                <button
                  key={c.name}
                  onClick={() => setColor(c.name)}
                  disabled={loading}
                  className={`relative w-9 h-9 rounded-full transition-all hover:scale-110 disabled:opacity-50 ${
                    color === c.name 
                      ? 'ring-2 ring-offset-2 ring-gray-900 scale-110' 
                      : 'hover:ring-2 hover:ring-offset-1 hover:ring-gray-300'
                  }`}
                  style={{ backgroundColor: c.hex }}
                  title={c.name}
                >
                  {color === c.name && (
                    <Check className="w-4 h-4 text-white absolute inset-0 m-auto drop-shadow" />
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Icon Picker */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Icon</label>
            <div className="grid grid-cols-6 gap-2">
              {ICONS.map((ic) => (
                <button
                  key={ic.name}
                  onClick={() => setIcon(ic.name)}
                  disabled={loading}
                  className={`p-2.5 rounded-lg border-2 transition-all hover:scale-105 disabled:opacity-50 ${
                    icon === ic.name 
                      ? 'border-blue-500 bg-blue-50 shadow-sm' 
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                  title={ic.name}
                >
                  <span className="text-xl">{ic.emoji}</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex gap-3 justify-end px-6 py-4 bg-gray-50 border-t border-gray-100">
          <button
            onClick={handleClose}
            disabled={loading}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleCreate}
            disabled={!name.trim() || loading}
            className="px-4 py-2 text-sm font-medium text-white bg-gray-900 rounded-lg hover:bg-gray-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Creating...
              </>
            ) : (
              'Create'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
