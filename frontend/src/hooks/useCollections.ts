'use client';

import { useState, useCallback, useEffect } from 'react';
import collectionsService, {
  Collection,
  CollectionDetail,
  CollectionSuggestion,
  UserContext,
  CollectionStats,
} from '@/services/collectionsService';

export const useCollections = () => {
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCollections = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await collectionsService.listCollections();
      setCollections(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load collections');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCollections();
  }, [fetchCollections]);

  const createCollection = useCallback(
    async (name: string, description?: string, color?: string, icon?: string) => {
      try {
        const newCollection = await collectionsService.createCollection(
          name,
          description,
          color,
          icon
        );
        setCollections((prev) => [...prev, newCollection]);
        return newCollection;
      } catch (err) {
        throw err;
      }
    },
    []
  );

  const deleteCollection = useCallback(async (collectionId: number) => {
    try {
      await collectionsService.deleteCollection(collectionId);
      setCollections((prev) => prev.filter((c) => c.id !== collectionId));
    } catch (err) {
      throw err;
    }
  }, []);

  const updateCollection = useCallback(
    async (collectionId: number, updates: Partial<Collection>) => {
      try {
        const updated = await collectionsService.updateCollection(
          collectionId,
          updates
        );
        setCollections((prev) =>
          prev.map((c) => (c.id === collectionId ? updated : c))
        );
        return updated;
      } catch (err) {
        throw err;
      }
    },
    []
  );

  return {
    collections,
    loading,
    error,
    fetchCollections,
    createCollection,
    deleteCollection,
    updateCollection,
  };
};

export const useCollectionDetail = (collectionId: number | null) => {
  const [collection, setCollection] = useState<CollectionDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!collectionId) return;

    const fetchCollection = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await collectionsService.getCollection(collectionId);
        setCollection(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load collection');
      } finally {
        setLoading(false);
      }
    };

    fetchCollection();
  }, [collectionId]);

  const addMemory = useCallback(
    async (memoryId: number) => {
      if (!collectionId) return;
      try {
        await collectionsService.addMemoryToCollection(collectionId, memoryId);
        // Refetch collection to update memories
        const updated = await collectionsService.getCollection(collectionId);
        setCollection(updated);
      } catch (err) {
        throw err;
      }
    },
    [collectionId]
  );

  const removeMemory = useCallback(
    async (memoryId: number) => {
      if (!collectionId) return;
      try {
        await collectionsService.removeMemoryFromCollection(
          collectionId,
          memoryId
        );
        setCollection((prev) =>
          prev
            ? {
                ...prev,
                memories: prev.memories.filter((m) => m.id !== memoryId),
              }
            : null
        );
      } catch (err) {
        throw err;
      }
    },
    [collectionId]
  );

  return { collection, loading, error, addMemory, removeMemory };
};

export const useSuggestions = () => {
  const [suggestions, setSuggestions] = useState<CollectionSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSuggestions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await collectionsService.getPendingSuggestions();
      setSuggestions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load suggestions');
    } finally {
      setLoading(false);
    }
  }, []);

  const generateSuggestions = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await collectionsService.generateSuggestions();
      setSuggestions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate suggestions');
    } finally {
      setLoading(false);
    }
  }, []);

  const acceptSuggestion = useCallback(async (suggestionId: number) => {
    try {
      await collectionsService.acceptSuggestion(suggestionId);
      setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
    } catch (err) {
      throw err;
    }
  }, []);

  const rejectSuggestion = useCallback(async (suggestionId: number) => {
    try {
      await collectionsService.rejectSuggestion(suggestionId);
      setSuggestions((prev) => prev.filter((s) => s.id !== suggestionId));
    } catch (err) {
      throw err;
    }
  }, []);

  return {
    suggestions,
    loading,
    error,
    fetchSuggestions,
    generateSuggestions,
    acceptSuggestion,
    rejectSuggestion,
  };
};

export const useUserContext = () => {
  const [context, setContext] = useState<UserContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchContext = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await collectionsService.getUserContext();
      setContext(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load context');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContext();
  }, [fetchContext]);

  return { context, loading, error, refetch: fetchContext };
};

export const useCollectionStats = () => {
  const [stats, setStats] = useState<CollectionStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await collectionsService.getCollectionStats();
      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
};
