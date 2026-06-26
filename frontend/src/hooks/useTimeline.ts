'use client';

import { useState, useEffect, useCallback } from 'react';
import timelineService, {
  TimelineEvent,
  Milestone,
  AchievementsResponse,
  LearningStreak,
  KnowledgeEvolution,
  ForgottenMemories,
} from '@/services/timelineService';

export function useTimelineEvents() {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEvents = useCallback(async () => {
    try {
      setLoading(true);
      const data = await timelineService.getTimelineEvents();
      setEvents(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load timeline');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEvents();
  }, [fetchEvents]);

  return { events, loading, error, refetch: fetchEvents };
}

export function useTimelineGrouped(period: string = 'month') {
  const [grouped, setGrouped] = useState<Record<string, TimelineEvent[]>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await timelineService.getTimelineGrouped(period);
        setGrouped(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load grouped timeline');
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, [period]);

  return { grouped, loading, error };
}

export function useMemoryTimeline(memoryId: number) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await timelineService.getMemoryTimeline(memoryId);
        setEvents(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load memory timeline');
      } finally {
        setLoading(false);
      }
    };

    if (memoryId) {
      fetch();
    }
  }, [memoryId]);

  return { events, loading, error };
}

export function useMilestones() {
  const [milestones, setMilestones] = useState<Milestone | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await timelineService.getMilestones();
        setMilestones(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load milestones');
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, []);

  return { milestones, loading, error };
}

export function useAchievements() {
  const [achievements, setAchievements] = useState<AchievementsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await timelineService.getAchievements();
        setAchievements(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load achievements');
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, []);

  return { achievements, loading, error };
}

export function useLearningStreak() {
  const [streak, setStreak] = useState<LearningStreak | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    try {
      setLoading(true);
      const data = await timelineService.getLearningStreak();
      setStreak(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load streak');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return { streak, loading, error, refetch };
}

export function useKnowledgeEvolution(months: number = 12) {
  const [evolution, setEvolution] = useState<KnowledgeEvolution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await timelineService.getKnowledgeEvolution(months);
        setEvolution(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load evolution');
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, [months]);

  return { evolution, loading, error };
}

export function useForgottenMemories() {
  const [forgotten, setForgotten] = useState<ForgottenMemories | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetch = async () => {
      try {
        setLoading(true);
        const data = await timelineService.getForgottenMemories();
        setForgotten(data);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load forgotten memories');
      } finally {
        setLoading(false);
      }
    };

    fetch();
  }, []);

  return { forgotten, loading, error };
}
