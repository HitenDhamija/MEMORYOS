/**
 * Memory API Service
 * Handles all memory-related API calls
 */

import apiClient from './apiClient';

export interface Memory {
  id: number;
  file_id: string;
  user_id: number;
  original_filename: string;
  file_type: string;
  file_size: number;
  title: string;
  description?: string;
  tags?: string[] | string;
  is_processed: boolean;
  processing_status: string;
  upload_date: string;
  updated_at: string;
  processed_at?: string;
}

export interface MemoryListResponse {
  items: Memory[];
  total: number;
  skip: number;
  limit: number;
}

export interface MemorySearchParams {
  query?: string;
  tags?: string[];
  file_type?: string;
  skip?: number;
  limit?: number;
}

export interface StorageSummary {
  total_size: number;
  total_files: number;
  file_types: Record<string, number>;
  tags: string[];
}

class MemoryService {
  private baseUrl = '/v1/memories';

  /**
   * Upload a new memory file
   */
  async uploadMemory(
    file: File,
    title: string,
    description?: string,
    tags?: string
  ): Promise<Memory> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', title);
    if (description) formData.append('description', description);
    if (tags) formData.append('tags', tags);

    const response = await apiClient.post<Memory>(
      `${this.baseUrl}/upload`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  /**
   * List user's memories with pagination
   */
  async listMemories(skip: number = 0, limit: number = 20): Promise<MemoryListResponse> {
    const response = await apiClient.get<MemoryListResponse>(this.baseUrl, {
      params: { skip, limit },
    });

    return response.data;
  }

  /**
   * Search memories by metadata
   */
  async searchMemories(params: MemorySearchParams): Promise<MemoryListResponse> {
    const queryParams = {
      skip: params.skip || 0,
      limit: params.limit || 20,
      ...(params.query && { query: params.query }),
      ...(params.file_type && { file_type: params.file_type }),
      ...(params.tags && params.tags.length > 0 && { tags: params.tags.join(',') }),
    };

    const response = await apiClient.get<MemoryListResponse>(
      `${this.baseUrl}/search`,
      { params: queryParams }
    );

    return response.data;
  }

  /**
   * Get single memory by ID
   */
  async getMemory(id: number): Promise<Memory> {
    const response = await apiClient.get<Memory>(`${this.baseUrl}/${id}`);
    return response.data;
  }

  /**
   * Update memory metadata
   */
  async updateMemory(
    id: number,
    updates: {
      title?: string;
      description?: string;
      tags?: string;
    }
  ): Promise<Memory> {
    const response = await apiClient.put<Memory>(`${this.baseUrl}/${id}`, updates);
    return response.data;
  }

  /**
   * Delete memory (soft delete)
   */
  async deleteMemory(id: number): Promise<void> {
    await apiClient.delete(`${this.baseUrl}/${id}`);
  }

  /**
   * Get tags for a specific memory
   */
  async getMemoryTags(id: number): Promise<string[]> {
    const response = await apiClient.get<string[]>(`${this.baseUrl}/${id}/tags`);
    return response.data;
  }

  /**
   * Add tags to memory
   */
  async addTags(id: number, tags: string[]): Promise<Memory> {
    const response = await apiClient.post<Memory>(
      `${this.baseUrl}/${id}/tags`,
      { tags }
    );
    return response.data;
  }

  /**
   * Remove specific tag from memory
   */
  async removeTag(id: number, tag: string): Promise<Memory> {
    const response = await apiClient.delete<Memory>(
      `${this.baseUrl}/${id}/tags/${encodeURIComponent(tag)}`
    );
    return response.data;
  }

  /**
   * Download memory file
   */
  async downloadMemory(id: number, filename: string): Promise<void> {
    const response = await apiClient.get(`${this.baseUrl}/${id}/download`, {
      responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.parentNode?.removeChild(link);
    window.URL.revokeObjectURL(url);
  }

  /**
   * Get storage summary and analytics
   */
  async getStorageSummary(): Promise<StorageSummary> {
    const response = await apiClient.get<StorageSummary>(
      `${this.baseUrl}/stats/summary`
    );
    return response.data;
  }

  /**
   * Format file size for display
   */
  static formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 B';

    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  }

  /**
   * Get file icon based on file type
   */
  static getFileIcon(fileType: string): string {
    const icons: Record<string, string> = {
      pdf: '📄',
      image: '🖼️',
      txt: '📝',
      md: '📋',
      bookmark: '🔖',
      other: '📎',
    };
    return icons[fileType] || icons.other;
  }

  /**
   * Format date for display
   */
  static formatDate(dateString: string): string {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  }

  /**
   * Get status badge color
   */
  static getStatusColor(status: string): string {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      uploaded: 'bg-blue-100 text-blue-800',
      processing: 'bg-purple-100 text-purple-800',
      processed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
    };
    return colors[status] || colors.pending;
  }
}

export default new MemoryService();
