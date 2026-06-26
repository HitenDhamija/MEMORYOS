/**
 * Auth layout with Apple-style tile design.
 */

import { Brain } from 'lucide-react';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex">
      {/* Left tile - dark product showcase */}
      <div className="hidden lg:flex flex-1 apple-tile-dark items-center justify-center relative overflow-hidden">
        <div className="relative z-10 text-center max-w-md px-8">
          <div className="flex items-center justify-center gap-3 mb-8">
            <Brain className="w-10 h-10 text-apple-body-dark" />
            <span className="text-apple-display-lg text-apple-body-dark">
              MemoryOS
            </span>
          </div>

          <h1 className="text-apple-display-lg text-apple-body-dark mb-4">
            Your AI-Powered
            <br />
            Knowledge OS
          </h1>

          <p className="text-apple-lead text-apple-muted mb-12">
            Upload, organize, and discover knowledge using semantic search and AI-powered insights.
          </p>

          <div className="space-y-4 text-left">
            {[
              { icon: '🧠', text: 'AI-powered semantic search' },
              { icon: '📊', text: 'Track your learning journey' },
              { icon: '🔒', text: 'End-to-end encryption' },
              { icon: '⚡', text: 'Instant document processing' },
            ].map((feature, i) => (
              <div key={i} className="flex items-center gap-4 text-apple-body-dark/80">
                <span className="text-xl">{feature.icon}</span>
                <span className="text-apple-body">{feature.text}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right tile - form on parchment */}
      <div className="flex-1 flex items-center justify-center px-8 py-12 apple-tile-parchment relative">
        {/* Mobile logo */}
        <div className="lg:hidden absolute top-8 left-8">
          <div className="flex items-center gap-2">
            <Brain className="w-6 h-6 text-apple-blue" />
            <span className="text-apple-tagline text-apple-ink">MemoryOS</span>
          </div>
        </div>

        <div className="w-full max-w-[400px] animate-fade-in">
          {children}
        </div>
      </div>
    </div>
  );
}
