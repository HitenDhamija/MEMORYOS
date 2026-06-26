'use client';

import { useState, useCallback, useEffect } from 'react';
import discoveryService, {
  MemoryRecommendations,
  DiscoveryResponse,
  SearchResponse,
} from '@/services/discoveryService';

export const useMemoryRecommendations = (memoryId: number | null) => {
  const [recommendations, setRecommendations] = useState<MemoryRecommendations | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRecommendations = useCallback(async (topK: number = 5) => {
    if (!memoryId) return;
    
    try {
      setLoading(true);
      setError(null);
      const data = await discoveryService.getRecommendations(memoryId, topK);
      setRecommendations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch recommendations');
    } finally {
      setLoading(false);
    }
  }, [memoryId]);

  useEffect(() => {
    if (memoryId) {
      fetchRecommendations();
    }
  }, [memoryId, fetchRecommendations]);

  return { recommendations, loading, error, refetch: fetchRecommendations };
};

export const useDiscoveryExplore = () => {
  const [discovery, setDiscovery] = useState<DiscoveryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const explore = useCallback(async (limit: number = 20, minSimilarity: number = 0.5) => {
    try {
      setLoading(true);
      setError(null);
      const data = await discoveryService.exploreMemories(limit, minSimilarity);
      setDiscovery(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to explore memories');
    } finally {
      setLoading(false);
    }
  }, []);

  return { discovery, loading, error, explore };
};

export const useSemanticSearch = () => {
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(
    async (query: string, topK: number = 10, minSimilarity: number = 0.3) => {
      if (!query.trim()) {
        setResults(null);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const data = await discoveryService.semanticSearch(query, topK, minSimilarity);
        setResults(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Search failed');
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const reset = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return { results, loading, error, search, reset };
};
