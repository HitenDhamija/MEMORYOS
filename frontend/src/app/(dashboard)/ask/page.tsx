'use client';

import React, { useState, useEffect, useRef } from 'react';
import { 
  Send, Loader2, Sparkles, ChevronDown, ChevronUp, FileText, Folder, 
  Download, Pencil, GitCompare, MessageCircle, 
  ArrowRight
} from 'lucide-react';
import { useRouter } from 'next/navigation';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import qaService, { QASource, QAAction, SuggestedQuestion } from '@/services/qaService';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  sources?: QASource[];
  actions?: QAAction[];
  followUpQuestions?: string[];
  confidence?: number;
  documentsSearched?: number;
  timestamp: Date;
}

export default function AskPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<SuggestedQuestion[]>([]);
  const [suggestionsLoading, setSuggestionsLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const loadSuggestions = async () => {
      try {
        const data = await qaService.getSuggestedQuestions();
        setSuggestions(data);
      } catch {
      } finally {
        setSuggestionsLoading(false);
      }
    };
    loadSuggestions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (question: string) => {
    if (!question.trim() || loading) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: question.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const result = await qaService.askQuestion(question.trim());

      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        type: 'assistant',
        content: result.answer,
        sources: result.sources,
        actions: result.actions,
        followUpQuestions: result.follow_up_questions,
        confidence: result.confidence,
        documentsSearched: result.documents_searched,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      const content = typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: any) => d.msg || d.message || String(d)).join('; ')
          : 'Sorry, something went wrong while processing your question. Please try again.';
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        type: 'assistant',
        content,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(input);
    }
  };

  const handleAction = (action: QAAction) => {
    if (action.type === 'open_document' && action.memory_id) {
      router.push(`/memories/${action.memory_id}`);
    } else if (action.type === 'open_collection' && action.collection_id) {
      router.push(`/collections/${action.collection_id}`);
    } else if (action.type === 'download' && action.memory_id) {
      // Trigger download
      window.open(`/api/v1/memories/${action.memory_id}/download`, '_blank');
    } else if (action.type === 'summarize') {
      // Add as new question
      handleSubmit('Summarize the documents from my last query');
    } else if (action.type === 'compare') {
      handleSubmit('Compare the top two documents');
    } else if (action.type === 'ask_followup') {
      inputRef.current?.focus();
    }
  };

  const formatConfidence = (confidence: number) => {
    const pct = Math.round(confidence * 100);
    if (pct >= 70) return { label: 'High', color: 'text-green-600 bg-green-50' };
    if (pct >= 40) return { label: 'Medium', color: 'text-yellow-600 bg-yellow-50' };
    return { label: 'Low', color: 'text-gray-500 bg-gray-50' };
  };

  const getDocTypeIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'resume/cv': return '📋';
      case 'research paper': return '🔬';
      case 'report': return '📊';
      case 'article': return '📰';
      case 'tutorial': return '📚';
      case 'notes': return '📝';
      case 'interview prep': return '💼';
      case 'certificate': return '🎓';
      case 'documentation': return '📖';
      case 'cheat sheet': return '⚡';
      default: return '📄';
    }
  };

  const getActionIcon = (iconName: string) => {
    switch (iconName) {
      case 'file': return <FileText className="w-3.5 h-3.5" />;
      case 'folder': return <Folder className="w-3.5 h-3.5" />;
      case 'download': return <Download className="w-3.5 h-3.5" />;
      case 'pencil': return <Pencil className="w-3.5 h-3.5" />;
      case 'git-compare': return <GitCompare className="w-3.5 h-3.5" />;
      case 'sparkles': return <Sparkles className="w-3.5 h-3.5" />;
      case 'message-circle': return <MessageCircle className="w-3.5 h-3.5" />;
      default: return <ArrowRight className="w-3.5 h-3.5" />;
    }
  };

  const getMatchTypeBadge = (matchTypes: string[]) => {
    if (!matchTypes || matchTypes.length === 0) return null;
    
    const primary = matchTypes[0];
    const colors: Record<string, string> = {
      metadata: 'bg-blue-100 text-blue-700',
      collection: 'bg-purple-100 text-purple-700',
      tag: 'bg-green-100 text-green-700',
      topic: 'bg-orange-100 text-orange-700',
      keyword: 'bg-yellow-100 text-yellow-700',
      semantic: 'bg-indigo-100 text-indigo-700',
      knowledge_graph: 'bg-pink-100 text-pink-700',
    };

    return (
      <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${colors[primary] || 'bg-gray-100 text-gray-700'}`}>
        {primary}
      </span>
    );
  };

  const isEmpty = messages.length === 0;

  return (
    <ProtectedRoute>
      <div className="-mx-6 -mt-4 flex flex-col h-[calc(100vh-80px)]">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4 shrink-0">
          <div className="max-w-[800px] mx-auto">
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Sparkles className="w-6 h-6 text-purple-500" />
              Ask Your Knowledge Base
            </h1>
            <p className="text-sm text-gray-500 mt-1">
              Ask natural-language questions and get intelligent answers from your documents
            </p>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto px-6 py-6 min-h-0">
          <div className="max-w-[800px] mx-auto">
            {isEmpty && !loading ? (
              <div className="text-center py-12">
                <Sparkles className="w-16 h-16 text-purple-200 mx-auto mb-6" />
                <h2 className="text-xl font-semibold text-gray-700 mb-2">
                  What would you like to know?
                </h2>
                <p className="text-gray-500 mb-8 max-w-md mx-auto">
                  Ask questions about your uploaded documents and get intelligent answers synthesized from your knowledge base.
                </p>

                {!suggestionsLoading && suggestions.length > 0 && (
                  <div className="max-w-[600px] mx-auto">
                    <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">Suggested Questions</p>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {suggestions.map((s, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSubmit(s.question)}
                          className="text-left p-3 rounded-xl border border-gray-200 hover:border-purple-300 hover:bg-purple-50 transition text-sm text-gray-700 group"
                        >
                          <span className="flex items-center gap-2">
                            <Sparkles className="w-3.5 h-3.5 text-purple-400 group-hover:text-purple-600 shrink-0" />
                            {s.question}
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-6">
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[85%] ${msg.type === 'user' ? 'order-2' : 'order-1'}`}>
                      {/* Message bubble */}
                      <div className={`rounded-2xl px-5 py-4 ${
                        msg.type === 'user'
                          ? 'bg-gray-900 text-white'
                          : 'bg-white border border-gray-200 text-gray-800'
                      }`}>
                        {msg.type === 'assistant' ? (
                          <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>
                        ) : (
                          <div className="text-sm">{msg.content}</div>
                        )}
                      </div>

                      {/* Actions for assistant messages */}
                      {msg.type === 'assistant' && msg.actions && msg.actions.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {msg.actions.map((action, idx) => (
                            <button
                              key={idx}
                              onClick={() => handleAction(action)}
                              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-full transition"
                            >
                              {getActionIcon(action.icon)}
                              {action.label}
                            </button>
                          ))}
                        </div>
                      )}

                      {/* Follow-up questions */}
                      {msg.type === 'assistant' && msg.followUpQuestions && msg.followUpQuestions.length > 0 && (
                        <div className="mt-3">
                          <p className="text-xs text-gray-400 mb-2">Ask a follow-up:</p>
                          <div className="flex flex-wrap gap-2">
                            {msg.followUpQuestions.map((q, idx) => (
                              <button
                                key={idx}
                                onClick={() => handleSubmit(q)}
                                className="text-left text-xs px-3 py-1.5 rounded-full border border-gray-200 hover:border-purple-300 hover:bg-purple-50 text-gray-600 transition"
                              >
                                {q}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Sources panel */}
                      {msg.type === 'assistant' && msg.sources && msg.sources.length > 0 && (
                        <SourcesPanel
                          sources={msg.sources}
                          confidence={msg.confidence || 0}
                          documentsSearched={msg.documentsSearched || 0}
                          formatConfidence={formatConfidence}
                          getDocTypeIcon={getDocTypeIcon}
                          getMatchTypeBadge={getMatchTypeBadge}
                        />
                      )}
                    </div>
                  </div>
                ))}

                {/* Loading indicator */}
                {loading && (
                  <div className="flex justify-start">
                    <div className="bg-white border border-gray-200 rounded-2xl px-5 py-4">
                      <div className="flex items-center gap-3">
                        <Loader2 className="w-4 h-4 animate-spin text-purple-500" />
                        <span className="text-sm text-gray-500">Searching your knowledge base...</span>
                      </div>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Input Area */}
        <div className="bg-white border-t border-gray-200 px-6 py-4 shrink-0">
          <div className="max-w-[800px] mx-auto">
            <div className="flex items-center gap-3">
              <input
                ref={inputRef}
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question about your documents..."
                disabled={loading}
                className="flex-1 h-12 px-5 border border-gray-300 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:opacity-50 transition"
              />
              <button
                onClick={() => handleSubmit(input)}
                disabled={!input.trim() || loading}
                className="w-12 h-12 bg-gray-900 text-white rounded-full flex items-center justify-center hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition shrink-0"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-2 text-center">
              Answers are synthesized from your uploaded documents using semantic search
            </p>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}


function SourcesPanel({
  sources,
  confidence,
  documentsSearched,
  formatConfidence,
  getDocTypeIcon,
  getMatchTypeBadge,
}: {
  sources: QASource[];
  confidence: number;
  documentsSearched: number;
  formatConfidence: (c: number) => { label: string; color: string };
  getDocTypeIcon: (t: string) => string;
  getMatchTypeBadge: (types: string[]) => React.ReactNode;
}) {
  const [expanded, setExpanded] = useState(false);
  const conf = formatConfidence(confidence);

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-700 transition"
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {sources.length} source{sources.length !== 1 ? 's' : ''} · {documentsSearched} docs searched
        <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-medium ${conf.color}`}>
          {conf.label} confidence
        </span>
      </button>

      {expanded && (
        <div className="mt-2 space-y-2">
          {sources.map((source, idx) => (
            <div
              key={`${source.memory_id}-${idx}`}
              className="p-3 bg-gray-50 rounded-lg border border-gray-100 text-xs"
            >
              <div className="flex items-center gap-2 mb-1.5">
                <span>{getDocTypeIcon(source.document_type)}</span>
                <span className="font-medium text-gray-800 truncate">{source.filename}</span>
                {getMatchTypeBadge(source.match_types)}
                <span className="text-gray-400 ml-auto shrink-0">{Math.round(source.similarity * 100)}% match</span>
              </div>
              {source.preview && (
                <p className="text-gray-500 line-clamp-2">{source.preview}</p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
