import apiClient from '@/lib/apiClient';

export interface Collection {
  id: number;
  name: string;
  description?: string;
  color: string;
  icon: string;
  memory_count: number;
  is_archived?: boolean;
  is_favorite?: boolean;
  is_pinned?: boolean;
  cover_image_url?: string;
  created_at: string;
  updated_at: string;
}

export interface CollectionDetail extends Collection {
  memories: Memory[];
}

export interface Memory {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  status: string;
  upload_date: string;
}

export interface CollectionSuggestion {
  id: number;
  suggested_name: string;
  reasoning?: string;
  topics: string[];
  confidence_score: number;
  status: string;
  created_at: string;
}

export interface UserContext {
  frequently_used_topics: string[];
  recent_interests: string[];
  favorite_collections: string[];
  total_memories: number;
  total_collections: number;
}

export interface CollectionStats {
  total_collections: number;
  largest_collection?: {
    id: number;
    name: string;
    size: number;
  };
  recently_updated?: {
    id: number;
    name: string;
    updated_at: string;
  };
  average_size: number;
}

class CollectionsService {
  /**
   * Create a new collection
   */
  async createCollection(
    name: string,
    description?: string,
    color?: string,
    icon?: string
  ): Promise<Collection> {
    const response = await apiClient.post('/v1/collections', {
      name,
      description,
      color: color || 'blue',
      icon: icon || 'folder',
    });
    return response.data;
  }

  /**
   * List user's collections
   */
  async listCollections(skip?: number, limit?: number): Promise<Collection[]> {
    const response = await apiClient.get('/v1/collections', {
      params: { skip: skip || 0, limit: limit || 100 },
    });
    return response.data;
  }

  /**
   * Get collection details
   */
  async getCollection(collectionId: number): Promise<CollectionDetail> {
    const response = await apiClient.get(`/v1/collections/${collectionId}`);
    return response.data;
  }

  /**
   * Update a collection
   */
  async updateCollection(
    collectionId: number,
    updates: Partial<Collection>
  ): Promise<Collection> {
    const response = await apiClient.put(`/v1/collections/${collectionId}`, updates);
    return response.data;
  }

  /**
   * Delete a collection
   */
  async deleteCollection(collectionId: number): Promise<void> {
    await apiClient.delete(`/v1/collections/${collectionId}`);
  }

  /**
   * Add memory to collection
   */
  async addMemoryToCollection(
    collectionId: number,
    memoryId: number
  ): Promise<void> {
    await apiClient.post(`/v1/collections/${collectionId}/memories/${memoryId}`);
  }

  /**
   * Remove memory from collection
   */
  async removeMemoryFromCollection(
    collectionId: number,
    memoryId: number
  ): Promise<void> {
    await apiClient.delete(`/v1/collections/${collectionId}/memories/${memoryId}`);
  }

  /**
   * Get collections containing a memory
   */
  async getMemoryCollections(memoryId: number): Promise<Collection[]> {
    const response = await apiClient.get(`/v1/collections/${memoryId}/collections`);
    return response.data;
  }

  /**
   * Generate collection suggestions
   */
  async generateSuggestions(): Promise<CollectionSuggestion[]> {
    const response = await apiClient.post('/v1/collections/suggestions/generate');
    return response.data;
  }

  /**
   * Get pending suggestions
   */
  async getPendingSuggestions(): Promise<CollectionSuggestion[]> {
    const response = await apiClient.get('/v1/collections/suggestions/pending');
    return response.data;
  }

  /**
   * Accept a suggestion
   */
  async acceptSuggestion(suggestionId: number): Promise<Collection> {
    const response = await apiClient.post(
      `/v1/collections/suggestions/${suggestionId}/accept`
    );
    return response.data;
  }

  /**
   * Reject a suggestion
   */
  async rejectSuggestion(suggestionId: number): Promise<void> {
    await apiClient.post(`/v1/collections/suggestions/${suggestionId}/reject`);
  }

  /**
   * Get user context
   */
  async getUserContext(): Promise<UserContext> {
    const response = await apiClient.get('/v1/collections/context/interests');
    return response.data;
  }

  /**
   * Get collection statistics
   */
  async getCollectionStats(): Promise<CollectionStats> {
    const response = await apiClient.get('/v1/collections/stats/overview');
    return response.data;
  }

  /**
   * Search collections
   */
  async searchCollections(query: string, skip?: number, limit?: number): Promise<Collection[]> {
    const response = await apiClient.get('/v1/collections/search', {
      params: { q: query, skip: skip || 0, limit: limit || 100 },
    });
    return response.data;
  }

  /**
   * Filter collections
   */
  async filterCollections(params: {
    is_archived?: boolean;
    is_favorite?: boolean;
    is_pinned?: boolean;
    color?: string;
    sort_by?: string;
    sort_order?: string;
    skip?: number;
    limit?: number;
  }): Promise<Collection[]> {
    const response = await apiClient.get('/v1/collections/filter', { params });
    return response.data;
  }

  /**
   * Get smart collections
   */
  async getSmartCollections(): Promise<any[]> {
    const response = await apiClient.get('/v1/collections/smart');
    return response.data;
  }

  /**
   * Get smart collection memories
   */
  async getSmartCollectionMemories(ruleId: string, skip?: number, limit?: number): Promise<any[]> {
    const response = await apiClient.get(`/v1/collections/smart/${ruleId}`, {
      params: { skip: skip || 0, limit: limit || 100 },
    });
    return response.data;
  }

  /**
   * Convert smart collection to real collection
   */
  async convertSmartToCollection(ruleId: string): Promise<Collection> {
    const response = await apiClient.post(`/v1/collections/smart/${ruleId}/convert`);
    return response.data;
  }

  /**
   * Get collection overview
   */
  async getCollectionOverview(collectionId: number): Promise<any> {
    const response = await apiClient.get(`/v1/collections/${collectionId}/overview`);
    return response.data;
  }

  /**
   * Get related collections
   */
  async getRelatedCollections(collectionId: number, limit?: number): Promise<any[]> {
    const response = await apiClient.get(`/v1/collections/${collectionId}/related`, {
      params: { limit: limit || 5 },
    });
    return response.data;
  }

  /**
   * Get knowledge graph
   */
  async getKnowledgeGraph(): Promise<any> {
    const response = await apiClient.get('/v1/collections/knowledge-graph');
    return response.data;
  }

  /**
   * Generate rename suggestions
   */
  async generateRenameSuggestions(): Promise<CollectionSuggestion[]> {
    const response = await apiClient.post('/v1/collections/suggestions/rename');
    return response.data;
  }

  /**
   * Generate merge suggestions
   */
  async generateMergeSuggestions(): Promise<CollectionSuggestion[]> {
    const response = await apiClient.post('/v1/collections/suggestions/merge');
    return response.data;
  }

  /**
   * Accept rename suggestion
   */
  async acceptRenameSuggestion(suggestionId: number, newName: string): Promise<Collection> {
    const response = await apiClient.post(
      `/v1/collections/suggestions/${suggestionId}/accept-rename`,
      null,
      { params: { new_name: newName } }
    );
    return response.data;
  }

  /**
   * Accept merge suggestion
   */
  async acceptMergeSuggestion(suggestionId: number): Promise<Collection> {
    const response = await apiClient.post(
      `/v1/collections/suggestions/${suggestionId}/accept-merge`
    );
    return response.data;
  }

  /**
   * Bulk move memories
   */
  async bulkMoveMemories(memoryIds: number[], targetCollectionId: number): Promise<any> {
    const response = await apiClient.post('/v1/collections/bulk/move', {
      memory_ids: memoryIds,
      target_collection_id: targetCollectionId,
    });
    return response.data;
  }

  /**
   * Bulk delete memories from collection
   */
  async bulkDeleteMemories(collectionId: number, memoryIds: number[]): Promise<any> {
    const response = await apiClient.post('/v1/collections/bulk/delete', {
      memory_ids: memoryIds,
    }, { params: { collection_id: collectionId } });
    return response.data;
  }

  /**
   * Bulk archive collections
   */
  async bulkArchiveCollections(collectionIds: number[]): Promise<any> {
    const response = await apiClient.post('/v1/collections/bulk/archive', collectionIds);
    return response.data;
  }

  /**
   * Bulk favorite collections
   */
  async bulkFavoriteCollections(collectionIds: number[]): Promise<any> {
    const response = await apiClient.post('/v1/collections/bulk/favorite', collectionIds);
    return response.data;
  }
}

export default new CollectionsService();
