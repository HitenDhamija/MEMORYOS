import apiClient from '@/lib/apiClient';

export interface RelatedMemory {
  memory_id: number;
  filename: string;
  similarity_score: number;
}

export interface MemoryRecommendations {
  memory_id: number;
  filename: string;
  related_memories: RelatedMemory[];
  total_related: number;
}

export interface DiscoveryItem {
  memory_id: number;
  filename: string;
  related_memories: RelatedMemory[];
}

export interface DiscoveryResponse {
  memories: DiscoveryItem[];
  total_items: number;
}

export interface SearchResult {
  memory_id: number;
  filename: string;
  similarity_score: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
}

class DiscoveryService {
  /**
   * Get recommendations for a specific memory
   */
  async getRecommendations(
    memoryId: number,
    topK: number = 5
  ): Promise<MemoryRecommendations> {
    const response = await apiClient.get(
      `/v1/discovery/recommendations/${memoryId}?top_k=${topK}`
    );
    return response.data;
  }

  /**
   * Explore memory connections and discover related content
   */
  async exploreMemories(
    limit: number = 20,
    minSimilarity: number = 0.5
  ): Promise<DiscoveryResponse> {
    const response = await apiClient.get('/v1/discovery/explore', {
      params: {
        limit,
        min_similarity: minSimilarity,
      },
    });
    return response.data;
  }

  /**
   * Semantic search across memories
   */
  async semanticSearch(
    query: string,
    topK: number = 10,
    minSimilarity: number = 0.3
  ): Promise<SearchResponse> {
    const response = await apiClient.post('/v1/discovery/search', null, {
      params: {
        query,
        top_k: topK,
        min_similarity: minSimilarity,
      },
    });
    return response.data;
  }
}

export default new DiscoveryService();
