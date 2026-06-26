import apiClient from '@/lib/apiClient';

export interface QAAction {
  type: string;
  label: string;
  icon: string;
  memory_id?: number;
  collection_id?: number;
}

export interface QASource {
  memory_id: number;
  filename: string;
  similarity: number;
  preview: string;
  document_type: string;
  match_types: string[];
}

export interface QAResponse {
  answer: string;
  sources: QASource[];
  actions: QAAction[];
  follow_up_questions: string[];
  confidence: number;
  documents_searched: number;
}

export interface SuggestedQuestion {
  question: string;
  category: string;
}

class QAService {
  async askQuestion(question: string, topK: number = 10): Promise<QAResponse> {
    const response = await apiClient.post<QAResponse>('/v1/qa/ask', {
      question,
      top_k: topK,
    });
    return response.data;
  }

  async getSuggestedQuestions(): Promise<SuggestedQuestion[]> {
    const response = await apiClient.get<SuggestedQuestion[]>('/v1/qa/suggested-questions');
    return response.data;
  }
}

export default new QAService();
