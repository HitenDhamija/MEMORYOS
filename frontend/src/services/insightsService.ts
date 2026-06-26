/**
 * AI Insights Service
 * 
 * Generates AI-powered insights from user activity and knowledge evolution data.
 * This service analyzes existing data (no external AI calls) to provide intelligent
 * suggestions and observations about the user's learning patterns.
 */

import { apiClient } from '@/lib/apiClient';

export interface Insight {
  id: string;
  type: 'forgotten' | 'trending' | 'discovery' | 'milestone' | 'pattern' | 'suggestion';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  actionUrl?: string;
  actionLabel?: string;
  icon: 'alert' | 'trending' | 'lightbulb' | 'zap' | 'star' | 'bookmark';
  color: 'red' | 'orange' | 'yellow' | 'blue' | 'green' | 'purple';
}

export interface DashboardMetrics {
  currentStreak: number;
  longestStreak: number;
  totalMemories: number;
  totalCollections: number;
  recentDiscoveries: number;
  forgottenCount: number;
}

export interface DashboardData {
  metrics: DashboardMetrics;
  insights: Insight[];
  topTopics: Array<{ topic: string; count: number; trend: 'up' | 'down' | 'stable' }>;
  recentActivity: Array<{
    id: string;
    timestamp: string;
    action: string;
    description: string;
  }>;
  weeklyProgress: {
    uploads: number;
    searches: number;
    discoveries: number;
  };
}

class InsightsService {
  /**
   * Get comprehensive dashboard data with metrics and insights
   */
  async getDashboardData(): Promise<DashboardData> {
    try {
      const [streak, achievements, forgotten, evolution, timeline] = await Promise.all([
        apiClient.get('/v1/timeline/streak'),
        apiClient.get('/v1/timeline/achievements'),
        apiClient.get('/v1/timeline/forgotten'),
        apiClient.get('/v1/timeline/evolution?months=12'),
        apiClient.get('/v1/timeline/events?limit=20'),
      ]);

      const metrics = this.extractMetrics(streak.data, achievements.data);
      const insights = this.generateInsights(metrics, achievements.data, forgotten.data, evolution.data);
      const topTopics = this.extractTopics(evolution.data);
      const recentActivity = this.transformActivity(timeline.data);
      const weeklyProgress = this.calculateWeeklyProgress(timeline.data);

      return {
        metrics,
        insights,
        topTopics,
        recentActivity,
        weeklyProgress,
      };
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      return {
        metrics: {
          currentStreak: 0,
          longestStreak: 0,
          totalMemories: 0,
          totalCollections: 0,
          recentDiscoveries: 0,
          forgottenCount: 0,
        },
        insights: [],
        topTopics: [],
        recentActivity: [],
        weeklyProgress: { uploads: 0, searches: 0, discoveries: 0 },
      };
    }
  }

  /**
   * Extract key metrics from API responses
   */
  private extractMetrics(
    streakData: any,
    achievementsData: any,
  ): DashboardMetrics {
    return {
      currentStreak: streakData?.current_streak || 0,
      longestStreak: streakData?.longest_streak || 0,
      totalMemories: achievementsData?.progress?.memories?.current || achievementsData?.progress?.total_memories || 0,
      totalCollections: achievementsData?.progress?.collections?.current || achievementsData?.progress?.total_collections || 0,
      recentDiscoveries: achievementsData?.progress?.searches?.current || achievementsData?.progress?.total_searches || 0,
      forgottenCount: 0,
    };
  }

  /**
   * Generate AI insights from user data
   */
  private generateInsights(
    metrics: DashboardMetrics,
    achievements: any,
    forgotten: any,
    evolution: any,
  ): Insight[] {
    const insights: Insight[] = [];

    // Forgotten memories insight
    if (forgotten?.thirty_days > 0) {
      insights.push({
        id: 'forgotten-30',
        type: 'forgotten',
        title: `${forgotten.thirty_days} memories waiting to be reviewed`,
        description: 'You have memories not viewed in the last 30 days. Time to revisit them?',
        priority: forgotten.thirty_days > 5 ? 'high' : 'medium',
        actionUrl: '/timeline',
        actionLabel: 'Review forgotten',
        icon: 'alert',
        color: 'orange',
      });
    }

    // Trending topics insight
    const topicTrends = this.analyzeTrendingTopics(evolution);
    if (topicTrends.length > 0) {
      const topTrend = topicTrends[0];
      insights.push({
        id: 'trending-topic',
        type: 'trending',
        title: `${topTrend.topic} is trending`,
        description: `"${topTrend.topic}" has been your fastest-growing area of interest this month.`,
        priority: 'medium',
        actionUrl: `/search?q=${encodeURIComponent(topTrend.topic)}`,
        actionLabel: 'Explore',
        icon: 'trending',
        color: 'blue',
      });
    }

    // Milestone insight
    if (achievements?.progress) {
      const nextMilestone = this.findNextMilestone(achievements.progress);
      if (nextMilestone) {
        insights.push({
          id: 'milestone-progress',
          type: 'milestone',
          title: `${nextMilestone.label} coming up!`,
          description: `${nextMilestone.remaining} more ${nextMilestone.unit} to reach your next milestone.`,
          priority: 'low',
          actionUrl: '/timeline',
          actionLabel: 'View progress',
          icon: 'zap',
          color: 'green',
        });
      }
    }

    // Learning streak insight
    if (metrics.currentStreak > 7) {
      insights.push({
        id: 'streak-momentum',
        type: 'pattern',
        title: `${metrics.currentStreak} day streak! 🔥`,
        description: 'You\'re on fire! Keep the momentum going.',
        priority: 'low',
        icon: 'star',
        color: 'yellow',
      });
    }

    // Low activity insight
    if (metrics.currentStreak === 0) {
      insights.push({
        id: 'restart-streak',
        type: 'suggestion',
        title: 'Time to start a new streak',
        description: 'Upload a memory or discover something new to get back on track.',
        priority: 'medium',
        actionUrl: '/upload',
        actionLabel: 'Upload a memory',
        icon: 'lightbulb',
        color: 'purple',
      });
    }

    return insights.slice(0, 5); // Return top 5 insights
  }

  /**
   * Analyze trending topics from evolution data
   */
  private analyzeTrendingTopics(evolution: any[]): Array<{ topic: string; trend: number }> {
    const topicFrequency: { [key: string]: number } = {};

    evolution.forEach((period) => {
      const topics = (period.topics || '').split(',').filter((t: string) => t.trim());
      topics.forEach((topic: string) => {
        topicFrequency[topic.trim()] = (topicFrequency[topic.trim()] || 0) + 1;
      });
    });

    return Object.entries(topicFrequency)
      .map(([topic, count]) => ({ topic, trend: count }))
      .sort((a, b) => b.trend - a.trend)
      .slice(0, 3);
  }

  /**
   * Find next milestone to achieve
   */
  private findNextMilestone(progress: any): any {
    const milestones = [
      { label: '50 memories', value: 50, unit: 'memories', current: progress.total_memories },
      { label: '100 memories', value: 100, unit: 'memories', current: progress.total_memories },
      { label: '5 collections', value: 5, unit: 'collections', current: progress.total_collections },
      { label: '10 collections', value: 10, unit: 'collections', current: progress.total_collections },
    ];

    const nextMilestone = milestones.find((m) => m.current < m.value);
    if (nextMilestone) {
      return {
        label: nextMilestone.label,
        remaining: nextMilestone.value - nextMilestone.current,
        unit: nextMilestone.unit,
      };
    }
    return null;
  }

  /**
   * Extract top topics from evolution data
   */
  private extractTopics(evolution: any[]): Array<{ topic: string; count: number; trend: 'up' | 'down' | 'stable' }> {
    const topicMap: { [key: string]: { count: number; lastSeen: number } } = {};

    evolution.forEach((period, index) => {
      const topics = (period.topics || '').split(',').filter((t: string) => t.trim());
      topics.forEach((topic: string) => {
        const trimmed = topic.trim();
        if (!topicMap[trimmed]) {
          topicMap[trimmed] = { count: 0, lastSeen: -1 };
        }
        topicMap[trimmed].count++;
        topicMap[trimmed].lastSeen = index;
      });
    });

    return Object.entries(topicMap)
      .map(([topic, data]) => ({
        topic,
        count: data.count,
        trend: (data.lastSeen === 0 ? 'up' : data.lastSeen > evolution.length - 3 ? 'down' : 'stable') as 'up' | 'down' | 'stable',
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5);
  }

  /**
   * Transform timeline events into activity items
   */
  private transformActivity(events: any[]): Array<{
    id: string;
    timestamp: string;
    action: string;
    description: string;
  }> {
    const actionLabels: { [key: string]: string } = {
      upload: 'Uploaded memory',
      document_processed: 'Document processed',
      embedding_generated: 'Embeddings generated',
      collection_assigned: 'Added to collection',
      search: 'Searched for',
      discovery: 'Discovered similarity',
      collection_created: 'Created collection',
      memory_viewed: 'Reviewed memory',
    };

    return events
      .slice(0, 10)
      .map((event: any) => {
        let eventData = event.event_data;
        if (typeof eventData === 'string') {
          try { eventData = JSON.parse(eventData); } catch { eventData = {}; }
        }
        return {
          id: String(event.id || `event-${Math.random()}`),
          timestamp: event.event_date || new Date().toISOString(),
          action: actionLabels[event.event_type] || event.event_type,
          description: eventData?.title || eventData?.filename || eventData?.query || eventData?.collection_name || 'Activity',
        };
      });
  }

  /**
   * Calculate weekly progress metrics
   */
  private calculateWeeklyProgress(events: any[]): { uploads: number; searches: number; discoveries: number } {
    const oneWeekAgo = new Date();
    oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);

    let uploads = 0;
    let searches = 0;
    let discoveries = 0;

    events.forEach((event: any) => {
      const eventDate = new Date(event.event_date);
      if (eventDate > oneWeekAgo) {
        if (event.event_type === 'upload') uploads++;
        if (event.event_type === 'search') searches++;
        if (event.event_type === 'discovery') discoveries++;
      }
    });

    return { uploads, searches, discoveries };
  }

  /**
   * Get upcoming reminders and notifications
   */
  async getNotifications(): Promise<any[]> {
    try {
      const [forgotten, achievements] = await Promise.all([
        apiClient.get('/v1/timeline/forgotten'),
        apiClient.get('/v1/timeline/achievements'),
      ]);

      const notifications = [];

      if (forgotten.data?.thirty_days > 0) {
        notifications.push({
          id: 'forgotten-reminder',
          type: 'review_reminder',
          title: 'Review forgotten memories',
          message: `You have ${forgotten.data.thirty_days} memories not viewed in 30 days`,
          priority: 'high',
        });
      }

      if (achievements.data?.unlocked?.length > 0) {
        const latestUnlocked = achievements.data.unlocked[0];
        notifications.push({
          id: 'milestone-unlocked',
          type: 'milestone',
          title: 'Achievement unlocked!',
          message: `You've reached the ${latestUnlocked} milestone!`,
          priority: 'medium',
        });
      }

      return notifications;
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
      return [];
    }
  }
}

export const insightsService = new InsightsService();
