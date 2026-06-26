import { apiClient } from '@/lib/apiClient';

export interface TimelineEvent {
  id: number;
  event_type: string;
  event_date: string;
  memory_id?: number;
  collection_id?: number;
  event_data?: string;
}

export interface Milestone {
  first_upload: boolean;
  memories_50: boolean;
  memories_100: boolean;
  memories_500: boolean;
  collections_5: boolean;
  collections_10: boolean;
  searches_50: boolean;
  searches_100: boolean;
  first_upload_date?: string;
  memories_100_date?: string;
}

export interface Achievement {
  id: string;
  name: string;
  date?: string;
}

export interface AchievementsResponse {
  unlocked: Achievement[];
  progress: {
    memories: { current: number; targets: number[] };
    collections: { current: number; targets: number[] };
    searches: { current: number; targets: number[] };
  };
}

export interface LearningStreak {
  current_streak: number;
  longest_streak: number;
  total_uploads: number;
  total_searches: number;
  total_collections_created: number;
  last_activity_date?: string;
  streak_start_date?: string;
}

export interface KnowledgeEvolution {
  period: string;
  topics: string[];
  memory_count: number;
  search_count: number;
  collection_count: number;
  discovery_count: number;
}

export interface ForgottenMemories {
  thirty_days: number;
  sixty_days: number;
  ninety_days: number;
}

class TimelineService {
  async getTimelineEvents(
    startDate?: string,
    endDate?: string,
    eventTypes?: string,
    skip?: number,
    limit?: number
  ): Promise<TimelineEvent[]> {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (eventTypes) params.append('event_types', eventTypes);
    if (skip !== undefined) params.append('skip', skip.toString());
    if (limit !== undefined) params.append('limit', limit.toString());

    const response = await apiClient.get(
      `/v1/timeline/events?${params.toString()}`
    );
    return response.data;
  }

  async getTimelineGrouped(period: string = 'month'): Promise<Record<string, TimelineEvent[]>> {
    const response = await apiClient.get(`/v1/timeline/events/grouped?period=${period}`);
    return response.data;
  }

  async getMemoryTimeline(memoryId: number): Promise<TimelineEvent[]> {
    const response = await apiClient.get(`/v1/timeline/memory/${memoryId}/events`);
    return response.data;
  }

  async getMilestones(): Promise<Milestone> {
    const response = await apiClient.get('/v1/timeline/milestones');
    return response.data;
  }

  async getAchievements(): Promise<AchievementsResponse> {
    const response = await apiClient.get('/v1/timeline/achievements');
    return response.data;
  }

  async getLearningStreak(): Promise<LearningStreak> {
    const response = await apiClient.get('/v1/timeline/streak');
    return response.data;
  }

  async getKnowledgeEvolution(months: number = 12): Promise<KnowledgeEvolution[]> {
    const response = await apiClient.get(`/v1/timeline/evolution?months=${months}`);
    return response.data;
  }

  async getForgottenMemories(): Promise<ForgottenMemories> {
    const response = await apiClient.get('/v1/timeline/forgotten');
    return response.data;
  }

  async trackActivity(): Promise<{ success: boolean }> {
    const response = await apiClient.post('/v1/timeline/stripe-activity', {});
    return response.data;
  }
}

export default new TimelineService();
