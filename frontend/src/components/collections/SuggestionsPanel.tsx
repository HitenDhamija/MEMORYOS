/**
 * Suggestions Panel - Apple Design Language
 */

'use client';

import React, { useState } from 'react';
import { Sparkles, Check, X, Loader2 } from 'lucide-react';
import { CollectionSuggestion } from '@/services/collectionsService';

interface SuggestionsPanelProps {
  suggestions: CollectionSuggestion[];
  loading: boolean;
  onAccept: (id: number) => Promise<void>;
  onReject: (id: number) => Promise<void>;
}

export default function SuggestionsPanel({ suggestions, loading, onAccept, onReject }: SuggestionsPanelProps) {
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  const handleAccept = async (id: number) => {
    try {
      setActionLoading(id);
      await onAccept(id);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id: number) => {
    try {
      setActionLoading(id);
      await onReject(id);
    } finally {
      setActionLoading(null);
    }
  };

  const parseTopics = (topics: string[] | string): string[] => {
    if (Array.isArray(topics)) return topics;
    if (typeof topics === 'string' && topics) return topics.split(',').map(t => t.trim()).filter(Boolean);
    return [];
  };

  return (
    <div className="mb-6 bg-white rounded-xl border border-blue-200 p-5">
      <div className="flex items-center gap-2 mb-3">
        <Sparkles className="w-5 h-5 text-blue-600" />
        <h2 className="text-base font-semibold text-gray-900">Suggested Collections</h2>
      </div>
      <p className="text-sm text-gray-500 mb-4">Based on your memories, we suggest creating these collections:</p>
      
      {loading && suggestions.length === 0 ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-500">Generating suggestions...</span>
        </div>
      ) : (
        <div className="space-y-3">
          {suggestions.map((suggestion) => {
            const topics = parseTopics(suggestion.topics);
            return (
              <div key={suggestion.id} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="text-sm font-medium text-gray-900">{suggestion.suggested_name}</h3>
                    {suggestion.reasoning && (
                      <p className="text-xs text-gray-500 mt-1 line-clamp-2">{suggestion.reasoning}</p>
                    )}
                  </div>
                  <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs font-medium shrink-0">
                    {suggestion.confidence_score}%
                  </span>
                </div>
                {topics.length > 0 && (
                  <div className="mb-3 flex flex-wrap gap-1">
                    {topics.map((topic, i) => (
                      <span key={i} className="px-2 py-0.5 bg-white border border-gray-200 text-gray-600 text-xs rounded-full">{topic}</span>
                    ))}
                  </div>
                )}
                <div className="flex gap-2">
                  <button 
                    onClick={() => handleAccept(suggestion.id)} 
                    disabled={actionLoading === suggestion.id}
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-blue-600 text-white text-xs font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {actionLoading === suggestion.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                    {actionLoading === suggestion.id ? 'Creating...' : 'Accept'}
                  </button>
                  <button 
                    onClick={() => handleReject(suggestion.id)} 
                    disabled={actionLoading === suggestion.id}
                    className="flex-1 flex items-center justify-center gap-1.5 px-3 py-1.5 bg-white border border-gray-300 text-gray-700 text-xs font-medium rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
                  >
                    <X className="w-3.5 h-3.5" />
                    Reject
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
