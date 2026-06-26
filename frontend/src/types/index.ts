/**
 * TypeScript type definitions.
 */

export interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Memory {
  id: number;
  user_id: number;
  title: string;
  content: string;
  tags?: string;
  source?: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}
