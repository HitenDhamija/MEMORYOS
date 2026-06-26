/**
 * Memory Details Page - Apple Design Language
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { ArrowLeft, Loader2, AlertCircle, Download, Trash2, FileText, Folder } from 'lucide-react';
import Link from 'next/link';
import apiClient from '@/services/apiClient';
import AddToCollection from '@/components/collections/AddToCollection';

interface RelatedMemory {
  id: number;
  title: string;
  file_type: string;
  similarity_score: number;
  preview?: string;
  upload_date: string;
}

interface Collection {
  id: number;
  name: string;
  description?: string;
}

interface MemoryDetails {
  id: number;
  file_id: string;
  user_id: number;
  original_filename: string;
  file_type: string;
  file_size: number;
  title: string;
  description?: string;
  tags?: string[];
  upload_date: string;
  updated_at: string;
  is_processed: boolean;
  processing_status: string;
  processed_at?: string;
  processing_error?: string;
  extracted_text?: string;
  preview?: string;
  summary?: string;
  word_count: number;
  char_count: number;
  language: string;
  reading_time: number;
  topics?: Record<string, unknown>;
  doc_metadata?: Record<string, unknown>;
  document_structure?: Record<string, unknown>;
  document_overview?: string;
  topics_covered?: string[];
  key_concepts?: string[];
  intelligent_keywords?: string[];
  doc_intelligence_metadata?: {
    type?: string;
    domain?: string;
    difficulty?: string;
    estimated_reading_time?: string;
    pages?: number;
    contains_examples?: boolean;
    contains_exercises?: boolean;
    contains_formulas?: boolean;
    language?: string;
  };
  suggested_questions?: string[];
  learning_objectives?: string[];
  type_specific_section?: {
    label: string;
    items: string[];
  };
  confidence_scores?: Record<string, number>;
  knowledge_nodes?: Array<{
    title: string;
    description: string;
    keywords: string[];
    page_numbers?: number[];
  }>;
  related_memories?: RelatedMemory[];
}

export default function MemoryDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const memoryId = parseInt(params.id as string);
  const [memory, setMemory] = useState<MemoryDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [collections, setCollections] = useState<Collection[]>([]);

  function getTypeSectionIcon(type?: string): string {
    switch (type) {
      case 'Resume / CV': return '👤';
      case 'Research Paper': return '🔬';
      case 'Study Material': return '📖';
      case 'Technical Documentation': return '📚';
      case 'Book': return '📕';
      case 'Tutorial / Guide': return '🛠';
      case 'Lecture Notes': return '📝';
      case 'Cheat Sheet': return '⚡';
      default: return '🎯';
    }
  }

  useEffect(() => {
    const loadMemory = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get<MemoryDetails>(`/v1/memories/${memoryId}`);
        setMemory(response.data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load memory');
      } finally {
        setLoading(false);
      }
    };
    if (memoryId) loadMemory();
  }, [memoryId]);

  useEffect(() => {
    const loadCollections = async () => {
      try {
        const response = await apiClient.get<{ collections: Collection[] }>('/v1/collections', { params: { memory_id: memoryId } });
        setCollections(response.data.collections || []);
      } catch (err) {
        console.error('Failed to load collections:', err);
      }
    };
    if (memoryId) loadCollections();
  }, [memoryId]);

  const handleCollectionAdded = (collection: Collection) => {
    setCollections(prev => {
      if (prev.some(c => c.id === collection.id)) return prev;
      return [...prev, collection];
    });
  };

  const handleDownload = async () => {
    try {
      if (!memory) return;
      const response = await apiClient.get(`/v1/memories/${memoryId}/download`, { responseType: 'blob' });
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = memory.original_filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Download failed');
    }
  };

  const handleDelete = async () => {
    if (!confirm('Are you sure you want to delete this memory?')) return;
    try {
      await apiClient.delete(`/v1/memories/${memoryId}`);
      router.push('/memories');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    }
  };

  if (loading) {
    return (
      <div className="apple-tile-light flex items-center justify-center min-h-[60vh]">
        <div className="flex items-center gap-3">
          <Loader2 className="w-6 h-6 animate-spin text-apple-blue" />
          <span className="text-apple-body text-apple-ink-48">Loading memory details…</span>
        </div>
      </div>
    );
  }

  if (error || !memory) {
    return (
      <div className="apple-tile-light p-4 min-h-[60vh]">
        <div className="max-w-[800px] mx-auto">
          <button onClick={() => router.back()} className="mb-4 flex items-center gap-2 apple-link">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <div className="p-4 bg-red-50 border border-red-200 rounded-apple-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
            <div>
              <h3 className="font-medium text-red-900">Error</h3>
              <p className="text-red-700 text-apple-caption">{error || 'Memory not found'}</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const hasAnalysis = memory.document_overview || memory.topics_covered?.length || memory.intelligent_keywords?.length;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <section className="apple-tile-light">
        <div className="max-w-[720px] mx-auto">
          <button onClick={() => router.back()} className="mb-4 flex items-center gap-2 apple-link transition-colors">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <div className="flex items-center gap-3 mb-1">
            <FileText className="w-7 h-7 text-apple-blue flex-shrink-0" />
            <h1 className="text-apple-display-lg text-apple-ink">{memory.title || memory.original_filename}</h1>
          </div>
          <p className="text-apple-caption text-apple-ink-48 ml-10">
            Uploaded {new Date(memory.upload_date).toLocaleDateString()} · {memory.file_type.toUpperCase()}
          </p>
        </div>
      </section>

      {/* Content */}
      <section className="apple-tile-parchment">
        <div className="max-w-[720px] mx-auto space-y-0">

          {/* ── Overview ── */}
          {(memory.document_overview || memory.summary) && (
            <>
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                  <span className="text-lg">📝</span> Overview
                </h2>
                <p className="text-apple-body text-apple-ink leading-relaxed">{memory.document_overview || memory.summary}</p>
              </div>
              <div className="border-b border-apple-hairline" />
            </>
          )}

          {/* ── Topics ── */}
          {memory.topics_covered && memory.topics_covered.length > 0 && (
            <>
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                  <span className="text-lg">📚</span> Topics
                </h2>
                <div className="space-y-2">
                  {memory.topics_covered.map((topic, idx) => (
                    <div key={idx} className="flex items-center gap-2.5">
                      <span className="w-5 h-5 rounded-full bg-apple-blue/10 flex items-center justify-center flex-shrink-0">
                        <span className="text-apple-blue text-xs font-semibold">✓</span>
                      </span>
                      <span className="text-apple-body text-apple-ink">{topic}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="border-b border-apple-hairline" />
            </>
          )}

          {/* ── Keywords ── */}
          {memory.intelligent_keywords && memory.intelligent_keywords.length > 0 && (
            <>
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                  <span className="text-lg">🏷</span> Keywords
                </h2>
                <div className="flex flex-wrap gap-x-1 gap-y-1">
                  {memory.intelligent_keywords.slice(0, 12).map((kw, idx) => (
                    <span key={idx} className="text-apple-body text-apple-ink-48">
                      {kw}{idx < Math.min(memory.intelligent_keywords!.length, 12) - 1 ? ' •' : ''}
                    </span>
                  ))}
                </div>
              </div>
              <div className="border-b border-apple-hairline" />
            </>
          )}

          {/* ── Insights (metadata) ── */}
          {memory.doc_intelligence_metadata && (
            <>
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-4 flex items-center gap-2">
                  <span className="text-lg">📊</span> Insights
                </h2>
                <div className="space-y-3">
                  {memory.doc_intelligence_metadata.type && (
                    <div className="flex justify-between items-center">
                      <span className="text-apple-body text-apple-ink-48">Document Type</span>
                      <span className="text-apple-body-strong text-apple-ink">{memory.doc_intelligence_metadata.type}</span>
                    </div>
                  )}
                  {memory.doc_intelligence_metadata.pages && memory.doc_intelligence_metadata.pages > 0 && (
                    <div className="flex justify-between items-center">
                      <span className="text-apple-body text-apple-ink-48">Pages</span>
                      <span className="text-apple-body-strong text-apple-ink">{memory.doc_intelligence_metadata.pages}</span>
                    </div>
                  )}
                  {memory.word_count > 0 && (
                    <div className="flex justify-between items-center">
                      <span className="text-apple-body text-apple-ink-48">Words</span>
                      <span className="text-apple-body-strong text-apple-ink">{memory.word_count.toLocaleString()}</span>
                    </div>
                  )}
                  {memory.doc_intelligence_metadata.difficulty && memory.doc_intelligence_metadata.difficulty !== 'General' && (
                    <div className="flex justify-between items-center">
                      <span className="text-apple-body text-apple-ink-48">Difficulty</span>
                      <span className="text-apple-body-strong text-apple-ink">{memory.doc_intelligence_metadata.difficulty}</span>
                    </div>
                  )}
                  {memory.doc_intelligence_metadata.domain && memory.doc_intelligence_metadata.domain !== 'General' && (
                    <div className="flex justify-between items-center">
                      <span className="text-apple-body text-apple-ink-48">Domain</span>
                      <span className="text-apple-body-strong text-apple-ink">{memory.doc_intelligence_metadata.domain}</span>
                    </div>
                  )}
                  {memory.doc_intelligence_metadata.language && (
                    <div className="flex justify-between items-center">
                      <span className="text-apple-body text-apple-ink-48">Language</span>
                      <span className="text-apple-body-strong text-apple-ink">{memory.doc_intelligence_metadata.language}</span>
                    </div>
                  )}
                  {memory.reading_time > 0 && (
                    <div className="flex justify-between items-center">
                      <span className="text-apple-body text-apple-ink-48">Reading Time</span>
                      <span className="text-apple-body-strong text-apple-ink">{memory.reading_time} min</span>
                    </div>
                  )}
                  {memory.doc_intelligence_metadata.contains_examples !== undefined && (
                    <div className="flex justify-between items-center">
                      <span className="text-apple-body text-apple-ink-48">Contains Examples</span>
                      <span className="text-apple-body-strong text-apple-ink">{memory.doc_intelligence_metadata.contains_examples ? '✓' : '—'}</span>
                    </div>
                  )}
                  {memory.doc_intelligence_metadata.contains_exercises !== undefined && (
                    <div className="flex justify-between items-center">
                      <span className="text-apple-body text-apple-ink-48">Contains Exercises</span>
                      <span className="text-apple-body-strong text-apple-ink">{memory.doc_intelligence_metadata.contains_exercises ? '✓' : '—'}</span>
                    </div>
                  )}
                  {memory.doc_intelligence_metadata.contains_formulas !== undefined && (
                    <div className="flex justify-between items-center">
                      <span className="text-apple-body text-apple-ink-48">Contains Formulas</span>
                      <span className="text-apple-body-strong text-apple-ink">{memory.doc_intelligence_metadata.contains_formulas ? '✓' : '—'}</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="border-b border-apple-hairline" />
            </>
          )}

          {/* ── Type-Specific Section (Candidate Highlights, Research Contributions, etc.) ── */}
          {memory.type_specific_section && memory.type_specific_section.items.length > 0 && (
            <>
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                  <span className="text-lg">{getTypeSectionIcon(memory.doc_intelligence_metadata?.type)}</span> {memory.type_specific_section.label}
                </h2>
                <div className="space-y-2">
                  {memory.type_specific_section.items.map((item, idx) => (
                    <div key={idx} className="flex items-start gap-2.5">
                      <span className="w-5 h-5 rounded-full bg-emerald-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-emerald-600 text-xs font-semibold">✓</span>
                      </span>
                      <span className="text-apple-body text-apple-ink">{item}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="border-b border-apple-hairline" />
            </>
          )}

          {/* ── Fallback: Learning Objectives (if type_specific_section is empty) ── */}
          {(!memory.type_specific_section || memory.type_specific_section.items.length === 0) && memory.learning_objectives && memory.learning_objectives.length > 0 && (
            <>
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                  <span className="text-lg">🎯</span> Learning Objectives
                </h2>
                <div className="space-y-2">
                  {memory.learning_objectives.map((obj, idx) => (
                    <div key={idx} className="flex items-start gap-2.5">
                      <span className="w-5 h-5 rounded-full bg-emerald-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-emerald-600 text-xs font-semibold">✓</span>
                      </span>
                      <span className="text-apple-body text-apple-ink">{obj}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div className="border-b border-apple-hairline" />
            </>
          )}

          {/* ── Ask this document ── */}
          {memory.suggested_questions && memory.suggested_questions.length > 0 && (
            <>
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                  <span className="text-lg">💬</span> Ask this document
                </h2>
                <div className="space-y-2">
                  {memory.suggested_questions.slice(0, 5).map((q, idx) => (
                    <Link
                      key={idx}
                      href={`/ask?q=${encodeURIComponent(q)}`}
                      className="flex items-start gap-2.5 group cursor-pointer"
                    >
                      <span className="text-apple-blue mt-0.5 flex-shrink-0">•</span>
                      <span className="text-apple-body text-apple-ink group-hover:text-apple-blue transition-colors">{q}</span>
                    </Link>
                  ))}
                </div>
              </div>
              <div className="border-b border-apple-hairline" />
            </>
          )}

          {/* ── Fallback: show old stats if no new analysis ── */}
          {!hasAnalysis && (
            <>
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-4 flex items-center gap-2">
                  <span className="text-lg">📊</span> Document Info
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {[
                    { label: 'Status', value: memory.processing_status },
                    { label: 'File Type', value: memory.file_type },
                    { label: 'File Size', value: `${(memory.file_size / 1024).toFixed(1)} KB` },
                    { label: 'Language', value: memory.language },
                    { label: 'Words', value: String(memory.word_count || 0) },
                    { label: 'Characters', value: String(memory.char_count || 0) },
                    { label: 'Reading Time', value: `${memory.reading_time || 0} min` },
                  ].map((item, i) => (
                    <div key={i}>
                      <p className="text-apple-caption text-apple-ink-48 mb-1">{item.label}</p>
                      <p className="text-apple-body-strong text-apple-ink capitalize">{item.value}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div className="border-b border-apple-hairline" />
            </>
          )}

          {/* ── Actions ── */}
          <div className="py-5">
            <div className="flex flex-wrap gap-3">
              <AddToCollection
                memoryId={memoryId}
                currentCollectionIds={collections.map(c => c.id)}
                onAdded={handleCollectionAdded}
              />
              <button onClick={handleDownload} className="apple-btn-primary"><Download className="w-4 h-4 mr-2" /> Download</button>
              <button onClick={handleDelete} className="apple-btn-secondary text-red-600 border-red-300 hover:bg-red-50"><Trash2 className="w-4 h-4 mr-2" /> Delete</button>
            </div>
          </div>

          {/* ── Tags (if any) ── */}
          {memory.tags && memory.tags.length > 0 && (
            <>
              <div className="border-b border-apple-hairline" />
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                  <span className="text-lg">🏷</span> Tags
                </h2>
                <div className="flex flex-wrap gap-2">
                  {memory.tags.map((tag, idx) => (
                    <span key={idx} className="px-3 py-1 rounded-apple-pill border border-apple-hairline text-apple-caption text-apple-ink">{tag}</span>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ── Key Concepts ── */}
          {memory.key_concepts && memory.key_concepts.length > 0 && (
            <>
              <div className="border-b border-apple-hairline" />
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                  <span className="text-lg">💡</span> Key Concepts
                </h2>
                <div className="flex flex-wrap gap-2">
                  {memory.key_concepts.map((concept, idx) => (
                    <span key={idx} className="px-3 py-1.5 rounded-apple-pill bg-apple-blue/5 border border-apple-blue/20 text-apple-caption-strong text-apple-ink">
                      {concept}
                    </span>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ── Related Memories ── */}
          {memory.related_memories && memory.related_memories.length > 0 && (
            <>
              <div className="border-b border-apple-hairline" />
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                  <span className="text-lg">🔗</span> Related Memories
                </h2>
                <div className="space-y-2">
                  {memory.related_memories.map((related) => (
                    <Link key={related.id} href={`/memories/${related.id}`}>
                      <div className="group flex items-center justify-between p-3 rounded-apple-sm hover:bg-apple-parchment transition-colors">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-apple-body text-apple-ink group-hover:text-apple-blue line-clamp-1 transition-colors">{related.title}</h3>
                          <span className="text-apple-caption text-apple-ink-48">{Math.round(related.similarity_score * 100)}% match</span>
                        </div>
                        <span className="text-apple-blue text-apple-caption ml-2">→</span>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </>
          )}

          {/* ── Collections ── */}
          {collections.length > 0 && (
            <>
              <div className="border-b border-apple-hairline" />
              <div className="py-5">
                <h2 className="text-apple-body-strong text-apple-ink mb-3 flex items-center gap-2">
                  <span className="text-lg">📁</span> Collections
                </h2>
                <div className="flex flex-wrap gap-2">
                  {collections.map((collection) => (
                    <Link key={collection.id} href={`/collections/${collection.id}`}>
                      <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-apple-pill border border-apple-hairline text-apple-caption text-apple-ink hover:border-apple-blue hover:text-apple-blue transition-colors cursor-pointer">
                        <Folder className="w-3.5 h-3.5" />
                        {collection.name}
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            </>
          )}

        </div>
      </section>
    </div>
  );
}
