/**
 * Loading and States - Apple Design Language
 */

'use client';

import React from 'react';
import { Loader2 } from 'lucide-react';

export const CardSkeleton: React.FC = () => (
  <div className="apple-utility-card animate-pulse space-y-4">
    <div className="h-40 bg-apple-parchment rounded-apple-sm" />
    <div className="space-y-2">
      <div className="h-4 bg-apple-parchment rounded w-3/4" />
      <div className="h-4 bg-apple-parchment rounded w-1/2" />
    </div>
  </div>
);

export const TextSkeleton: React.FC<{ lines?: number }> = ({ lines = 3 }) => (
  <div className="space-y-3">
    {Array.from({ length: lines }).map((_, i) => (
      <div key={i} className="h-4 bg-apple-parchment rounded animate-pulse w-full" />
    ))}
  </div>
);

export const TableSkeleton: React.FC<{ rows?: number }> = ({ rows = 5 }) => (
  <div className="space-y-3">
    {Array.from({ length: rows }).map((_, i) => (
      <div key={i} className="h-12 bg-apple-parchment rounded animate-pulse" />
    ))}
  </div>
);

export const FullPageLoader: React.FC<{ message?: string }> = ({ message = 'Loading…' }) => (
  <div className="fixed inset-0 bg-white flex flex-col items-center justify-center z-50">
    <div className="text-center">
      <Loader2 className="w-12 h-12 animate-spin text-apple-blue mx-auto mb-4" />
      <p className="text-apple-body text-apple-ink">{message}</p>
    </div>
  </div>
);

export const CenterLoader: React.FC<{ message?: string }> = ({ message = 'Loading…' }) => (
  <div className="flex flex-col items-center justify-center py-16">
    <Loader2 className="w-10 h-10 animate-spin text-apple-blue mb-4" />
    <p className="text-apple-body text-apple-ink-48">{message}</p>
  </div>
);

export const EmptyState: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
  action?: { label: string; href: string };
}> = ({ icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center py-20 px-4">
    <div className="text-5xl mb-6">{icon}</div>
    <h3 className="text-apple-display-md text-apple-ink mb-2 text-center">{title}</h3>
    <p className="text-apple-body text-apple-ink-48 text-center mb-8 max-w-md">{description}</p>
    {action && <a href={action.href} className="apple-btn-primary">{action.label}</a>}
  </div>
);

export const NoMemoriesState: React.FC = () => (
  <EmptyState icon="📦" title="No memories yet" description="Start by uploading your first memory." action={{ label: 'Upload Memory', href: '/upload' }} />
);

export const NoCollectionsState: React.FC = () => (
  <EmptyState icon="📂" title="No collections yet" description="Create your first collection to organize memories." action={{ label: 'Create Collection', href: '/collections/new' }} />
);

export const NoResultsState: React.FC<{ query?: string }> = ({ query }) => (
  <EmptyState icon="🔍" title="No results found" description={query ? `No results for "${query}".` : 'No results to display.'} />
);

export const NoDiscoveriesState: React.FC = () => (
  <EmptyState icon="🧭" title="No discoveries yet" description="Upload more memories to get semantic discoveries." action={{ label: 'Upload Memory', href: '/upload' }} />
);

export const ErrorState: React.FC<{
  title?: string;
  message?: string;
  action?: { label: string; onClick: () => void };
}> = ({ title = 'Something went wrong', message = 'An error occurred.', action }) => (
  <div className="flex flex-col items-center justify-center py-16 px-4">
    <div className="text-5xl mb-6">❌</div>
    <h3 className="text-apple-display-md text-red-600 mb-2 text-center">{title}</h3>
    <p className="text-apple-body text-apple-ink-48 text-center mb-8 max-w-md">{message}</p>
    {action && <button onClick={action.onClick} className="apple-btn-primary">{action.label}</button>}
  </div>
);

export const ErrorCard: React.FC<{ title: string; message: string; action?: { label: string; onClick: () => void } }> = ({ title, message, action }) => (
  <div className="apple-utility-card border-red-200">
    <h3 className="text-apple-body-strong text-red-600 mb-2">{title}</h3>
    <p className="text-apple-caption text-red-500 mb-4">{message}</p>
    {action && <button onClick={action.onClick} className="apple-link text-apple-caption-strong">{action.label}</button>}
  </div>
);

export const StatusBadge: React.FC<{ status: 'success' | 'error' | 'warning' | 'info' | 'processing'; label: string }> = ({ status, label }) => {
  const config: Record<string, string> = {
    success: 'bg-green-50 text-green-600 border-green-200',
    error: 'bg-red-50 text-red-600 border-red-200',
    warning: 'bg-apple-parchment text-apple-ink border-apple-hairline',
    info: 'bg-apple-blue/10 text-apple-blue border-apple-blue/20',
    processing: 'bg-apple-parchment text-apple-ink-48 border-apple-hairline',
  };
  return (
    <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-apple-pill text-apple-fine-print font-semibold border ${config[status]}`}>
      {status === 'processing' && <Loader2 size={12} className="animate-spin" />}
      {label}
    </div>
  );
};

export const UploadProgress: React.FC<{ progress: number; filename: string }> = ({ progress, filename }) => (
  <div className="apple-utility-card">
    <div className="flex items-center justify-between mb-2">
      <p className="text-apple-body-strong text-apple-ink truncate">{filename}</p>
      <p className="text-apple-caption text-apple-ink-48 ml-2">{progress}%</p>
    </div>
    <div className="h-2 bg-apple-parchment rounded-full overflow-hidden">
      <div className="h-full bg-apple-blue transition-all duration-300 rounded-full" style={{ width: `${progress}%` }} />
    </div>
  </div>
);
