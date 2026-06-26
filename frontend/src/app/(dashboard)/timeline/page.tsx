/**
 * Timeline Page - Apple Design Language
 */

'use client';

import React from 'react';
import { Calendar, TrendingUp, Zap, Target, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import { useAchievements, useLearningStreak, useKnowledgeEvolution, useForgottenMemories } from '@/hooks/useTimeline';

export default function TimelinePage() {
  const { isAuthenticated } = useAuth();
  const { achievements, loading: achievementsLoading } = useAchievements();
  const { streak, loading: streakLoading } = useLearningStreak();
  const { evolution, loading: evolutionLoading } = useKnowledgeEvolution(12);
  const { forgotten, loading: forgottenLoading } = useForgottenMemories();

  if (!isAuthenticated) return <ProtectedRoute><div /></ProtectedRoute>;

  return (
    <div className="min-h-screen">
      {/* Header - Light Tile */}
      <section className="apple-tile-light">
        <div className="max-w-[980px] mx-auto">
          <h1 className="text-apple-display-lg text-apple-ink flex items-center gap-3">
            <Calendar className="w-8 h-8 text-apple-blue" />
            Knowledge Timeline
          </h1>
          <p className="text-apple-body text-apple-ink-48 mt-1">Visualize your learning journey and knowledge evolution</p>
        </div>
      </section>

      {/* Content - Parchment Tile */}
      <section className="apple-tile-parchment">
        <div className="max-w-[980px] mx-auto space-y-8">
          {/* Learning Streak */}
          {streakLoading ? (
            <div className="flex items-center justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-apple-blue mr-2" /><span className="text-apple-body text-apple-ink-48">Loading streak…</span></div>
          ) : streak ? (
            <div className="apple-utility-card">
              <h2 className="text-apple-display-md text-apple-ink mb-6 flex items-center gap-2">
                <Zap className="w-6 h-6 text-apple-blue" /> Learning Streak
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[
                  { label: 'Current Streak', value: streak.current_streak, sub: 'days' },
                  { label: 'Longest Streak', value: streak.longest_streak, sub: 'days' },
                  { label: 'Uploads', value: streak.total_uploads, sub: '' },
                  { label: 'Searches', value: streak.total_searches, sub: '' },
                ].map((item, i) => (
                  <div key={i} className="p-4 rounded-apple-lg border border-apple-hairline bg-apple-canvas">
                    <p className="text-apple-caption text-apple-ink-48">{item.label}</p>
                    <p className="text-apple-display-md text-apple-ink mt-1">{item.value}</p>
                    {item.sub && <p className="text-apple-fine-print text-apple-ink-48">{item.sub}</p>}
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* Achievements */}
          {achievementsLoading ? (
            <div className="flex items-center justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-apple-blue mr-2" /><span className="text-apple-body text-apple-ink-48">Loading achievements…</span></div>
          ) : achievements ? (
            <div className="apple-utility-card">
              <h2 className="text-apple-display-md text-apple-ink mb-6 flex items-center gap-2">
                <Target className="w-6 h-6 text-apple-blue" /> Achievements
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                <div className="p-4 rounded-apple-lg border border-apple-hairline bg-apple-canvas">
                  <p className="text-apple-caption-strong text-apple-ink-48 mb-2">Memory Milestones</p>
                  <p className="text-apple-display-md text-apple-ink">{achievements.progress.memories.current}</p>
                  <div className="flex gap-2 mt-3">
                    {achievements.progress.memories.targets.map((target) => (
                      <div key={target} className="px-2 py-1 text-apple-fine-print rounded-apple-pill border border-apple-hairline">
                        {target > achievements.progress.memories.current ? <>{target} →</> : <>✓ {target}</>}
                      </div>
                    ))}
                  </div>
                </div>
                <div className="p-4 rounded-apple-lg border border-apple-hairline bg-apple-canvas">
                  <p className="text-apple-caption-strong text-apple-ink-48 mb-2">Collection Milestones</p>
                  <p className="text-apple-display-md text-apple-ink">{achievements.progress.collections.current}</p>
                  <div className="flex gap-2 mt-3">
                    {achievements.progress.collections.targets.map((target) => (
                      <div key={target} className="px-2 py-1 text-apple-fine-print rounded-apple-pill border border-apple-hairline">
                        {target > achievements.progress.collections.current ? <>{target} →</> : <>✓ {target}</>}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
              <div className="border-t border-apple-hairline pt-4">
                <p className="text-apple-caption-strong text-apple-ink-48 mb-3">Unlocked</p>
                <div className="space-y-2">
                  {achievements.unlocked.length > 0 ? (
                    achievements.unlocked.map((achievement) => (
                      <div key={achievement.id} className="flex items-center justify-between p-3 rounded-apple-sm border border-apple-hairline">
                        <span className="text-apple-body text-apple-ink">{achievement.name}</span>
                        <span className="text-apple-fine-print text-apple-ink-48">{achievement.date ? new Date(achievement.date).toLocaleDateString() : 'Recently'}</span>
                      </div>
                    ))
                  ) : (
                    <p className="text-apple-body text-apple-ink-48">No achievements unlocked yet</p>
                  )}
                </div>
              </div>
            </div>
          ) : null}

          {/* Knowledge Evolution */}
          {evolutionLoading ? (
            <div className="flex items-center justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-apple-blue mr-2" /><span className="text-apple-body text-apple-ink-48">Loading evolution…</span></div>
          ) : evolution && evolution.length > 0 ? (
            <div className="apple-utility-card">
              <h2 className="text-apple-display-md text-apple-ink mb-6 flex items-center gap-2">
                <TrendingUp className="w-6 h-6 text-apple-blue" /> Knowledge Evolution
              </h2>
              <div className="space-y-4">
                {evolution.map((evo) => (
                  <div key={evo.period} className="p-4 rounded-apple-sm border border-apple-hairline">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-apple-body-strong text-apple-ink">{evo.period}</p>
                      <div className="flex gap-2">
                        <span className="px-2 py-1 text-apple-fine-print rounded-apple-pill border border-apple-hairline">{evo.memory_count} uploads</span>
                        <span className="px-2 py-1 text-apple-fine-print rounded-apple-pill border border-apple-hairline">{evo.search_count} searches</span>
                      </div>
                    </div>
                    {evo.topics.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {evo.topics.slice(0, 5).map((topic) => (
                          <span key={topic} className="px-2 py-1 text-apple-fine-print rounded-apple-pill border border-apple-hairline">{topic}</span>
                        ))}
                        {evo.topics.length > 5 && <span className="px-2 py-1 text-apple-fine-print text-apple-ink-48">+{evo.topics.length - 5} more</span>}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : null}

          {/* Forgotten Memories */}
          {forgottenLoading ? (
            <div className="flex items-center justify-center py-8"><Loader2 className="w-5 h-5 animate-spin text-apple-blue mr-2" /><span className="text-apple-body text-apple-ink-48">Loading forgotten memories…</span></div>
          ) : forgotten ? (
            <div className="apple-utility-card border-apple-blue/30">
              <h2 className="text-apple-display-md text-apple-ink mb-4 flex items-center gap-2">
                <AlertCircle className="w-6 h-6 text-apple-blue" /> Forgotten Memories
              </h2>
              <p className="text-apple-caption text-apple-ink-48 mb-4">These are memories you haven't revisited recently. Consider reviewing them to reinforce your knowledge.</p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { label: 'Not viewed in 30 days', value: forgotten.thirty_days },
                  { label: 'Not viewed in 60 days', value: forgotten.sixty_days },
                  { label: 'Not viewed in 90 days', value: forgotten.ninety_days },
                ].map((item, i) => (
                  <div key={i} className="p-4 rounded-apple-lg border border-apple-hairline bg-apple-canvas">
                    <p className="text-apple-caption text-apple-ink-48">{item.label}</p>
                    <p className="text-apple-display-md text-apple-ink mt-2">{item.value}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}
