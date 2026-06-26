/**
 * Dashboard Page - Apple Design Language
 */

'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { insightsService, type DashboardData, type Insight } from '@/services/insightsService';
import { OnboardingModal, useOnboarding } from '@/components/Onboarding';
import KnowledgeGraphCard from '@/components/KnowledgeGraphCard';
import { Loader2, TrendingUp, Zap, BookOpen, FolderOpen, Lightbulb, Clock, ArrowRight, Compass, Settings } from 'lucide-react';

const MetricCard: React.FC<{
  icon: React.ReactNode;
  label: string;
  value: number;
  unit?: string;
  color?: string;
}> = ({ icon, label, value, unit }) => (
  <div className="apple-utility-card">
    <div className="flex items-center gap-3 mb-3">
      <div className="text-apple-blue">{icon}</div>
      <span className="text-apple-caption-strong text-apple-ink">{label}</span>
    </div>
    <div className="flex items-baseline">
      <span className="text-apple-display-md text-apple-ink">{value}</span>
      {unit && <span className="text-apple-caption text-apple-ink-48 ml-2">{unit}</span>}
    </div>
  </div>
);

const InsightCard: React.FC<{ insight: Insight }> = ({ insight }) => {
  const iconMap: Record<string, string> = {
    alert: '⚠️',
    trending: '📈',
    lightbulb: '💡',
    zap: '⚡',
    star: '⭐',
    bookmark: '🔖',
  };

  return (
    <div className="apple-utility-card">
      <div className="flex items-start gap-3">
        <div className="text-xl">{iconMap[insight.icon]}</div>
        <div className="flex-1 min-w-0">
          <h3 className="text-apple-body-strong text-apple-ink mb-1">{insight.title}</h3>
          <p className="text-apple-caption text-apple-ink-48 mb-3">{insight.description}</p>
          {insight.actionUrl && (
            <Link href={insight.actionUrl} className="apple-link text-apple-caption-strong flex items-center gap-1">
              {insight.actionLabel || 'View'} <ArrowRight size={14} />
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};

const ActivityItem: React.FC<{ activity: any }> = ({ activity }) => (
  <div className="flex items-start gap-4 pb-4 border-b border-apple-hairline last:border-0">
    <div className="w-2 h-2 rounded-full bg-apple-blue mt-2 flex-shrink-0" />
    <div className="flex-1 min-w-0">
      <p className="text-apple-body-strong text-apple-ink">{activity.action}</p>
      <p className="text-apple-caption text-apple-ink-48 truncate">{activity.description}</p>
      <p className="text-apple-fine-print text-apple-ink-48 mt-1">
        {new Date(activity.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
      </p>
    </div>
  </div>
);

const TopicTag: React.FC<{ topic: string; count: number; trend: 'up' | 'down' | 'stable' }> = ({ topic, count }) => (
  <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-apple-pill border border-apple-hairline bg-apple-canvas">
    <span className="text-apple-caption text-apple-ink">{topic}</span>
    <span className="text-apple-fine-print text-apple-blue font-semibold">{count}</span>
  </div>
);

export default function DashboardPage() {
  const { user } = useAuth();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isOnboarded, completeOnboarding } = useOnboarding();
  const [showOnboarding, setShowOnboarding] = useState(false);

  useEffect(() => {
    if (!isOnboarded) setShowOnboarding(true);
  }, [isOnboarded]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const data = await insightsService.getDashboardData();
        setDashboardData(data);
        setError(null);
      } catch (err) {
        setError('Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="apple-tile-light flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-apple-blue mx-auto mb-4" />
          <p className="text-apple-body text-apple-ink-48">Loading your dashboard…</p>
        </div>
      </div>
    );
  }

  if (error || !dashboardData) {
    return (
      <div className="apple-tile-light flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <p className="text-apple-body text-apple-ink-48 mb-4">{error || 'Failed to load dashboard'}</p>
          <button onClick={() => window.location.reload()} className="apple-btn-primary">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const { metrics, insights, topTopics, recentActivity, weeklyProgress } = dashboardData;
  const greeting = `Good ${new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 18 ? 'afternoon' : 'evening'}, ${user?.username || 'User'}`;

  return (
    <ProtectedRoute>
      <div className="min-h-screen">
        {/* Header Tile - Light */}
        <section className="apple-tile-light">
          <div className="max-w-[980px] mx-auto">
            <div className="flex items-start justify-between mb-12">
              <div>
                <h1 className="text-apple-display-lg text-apple-ink mb-2">{greeting}</h1>
                <p className="text-apple-lead text-apple-ink-48">Welcome back to your learning journey</p>
              </div>
              <div className="flex gap-3">
                <Link href="/settings" className="apple-btn-pearl">
                  <Settings size={18} className="text-apple-ink-48" />
                </Link>
              </div>
            </div>

            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <MetricCard icon={<Zap className="w-5 h-5" />} label="Learning Streak" value={metrics.currentStreak} unit="days" color="orange" />
              <MetricCard icon={<BookOpen className="w-5 h-5" />} label="Total Memories" value={metrics.totalMemories} unit="files" color="blue" />
              <MetricCard icon={<Compass className="w-5 h-5" />} label="Discoveries" value={metrics.recentDiscoveries} unit="found" color="green" />
              <MetricCard icon={<FolderOpen className="w-5 h-5" />} label="Collections" value={metrics.totalCollections} unit="created" color="purple" />
              <MetricCard icon={<TrendingUp className="w-5 h-5" />} label="Weekly Activity" value={weeklyProgress.uploads + weeklyProgress.searches} unit="actions" color="indigo" />
              <MetricCard icon={<Clock className="w-5 h-5" />} label="Forgotten" value={metrics.forgottenCount} unit="to review" color="slate" />
            </div>
          </div>
        </section>

        {/* Quick Actions Tile - Parchment */}
        <section className="apple-tile-parchment">
          <div className="max-w-[980px] mx-auto">
            <h2 className="text-apple-display-md text-apple-ink mb-8">Quick Actions</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
              {[
                { icon: '📤', label: 'Upload', href: '/upload' },
                { icon: '🔍', label: 'Search', href: '/search' },
                { icon: '💡', label: 'Ask', href: '/ask' },
                { icon: '📂', label: 'Collections', href: '/collections' },
                { icon: '📊', label: 'Timeline', href: '/timeline' },
              ].map((action, i) => (
                <Link key={i} href={action.href}>
                  <div className="apple-utility-card text-center hover:border-apple-blue transition-colors cursor-pointer">
                    <div className="text-2xl mb-2">{action.icon}</div>
                    <p className="text-apple-caption-strong text-apple-ink">{action.label}</p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        </section>

        {/* Main Content Tile - Light */}
        <section className="apple-tile-light">
          <div className="max-w-[980px] mx-auto">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left column */}
              <div className="lg:col-span-2 space-y-8">
                <div>
                  <h2 className="text-apple-display-md text-apple-ink mb-6 flex items-center gap-2">
                    <Lightbulb className="w-6 h-6 text-apple-blue" />
                    AI Insights
                  </h2>
                  <div className="space-y-3">
                    {insights.length > 0 ? (
                      insights.map((insight) => <InsightCard key={insight.id} insight={insight} />)
                    ) : (
                      <p className="text-apple-body text-apple-ink-48 text-center py-8">No insights available yet. Start uploading memories!</p>
                    )}
                  </div>
                </div>

                <div>
                  <h2 className="text-apple-display-md text-apple-ink mb-6">Growing Topics</h2>
                  {topTopics.length > 0 ? (
                    <div className="flex flex-wrap gap-2">
                      {topTopics.map((topic) => (
                        <TopicTag key={topic.topic} topic={topic.topic} count={topic.count} trend={topic.trend} />
                      ))}
                    </div>
                  ) : (
                    <p className="text-apple-body text-apple-ink-48">Your topics will appear as you upload memories.</p>
                  )}
                </div>

                <KnowledgeGraphCard />
              </div>

              {/* Right column */}
              <div>
                <div className="apple-utility-card sticky top-24">
                  <h2 className="text-apple-body-strong text-apple-ink mb-6 flex items-center gap-2">
                    <Clock className="w-5 h-5 text-apple-blue" />
                    Recent Activity
                  </h2>
                  <div>
                    {recentActivity.length > 0 ? (
                      recentActivity.slice(0, 8).map((activity) => <ActivityItem key={activity.id} activity={activity} />)
                    ) : (
                      <p className="text-apple-body text-apple-ink-48 text-center py-8">No recent activity.</p>
                    )}
                    <Link href="/timeline" className="apple-link text-apple-caption-strong mt-4 flex items-center gap-1">
                      View all activity <ArrowRight size={14} />
                    </Link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <OnboardingModal isOpen={showOnboarding} onClose={() => setShowOnboarding(false)} onComplete={completeOnboarding} />
    </ProtectedRoute>
  );
}
