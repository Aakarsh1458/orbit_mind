import { request } from './client';
import { ConversationHistoryResponse, ConversationSummary } from '../types/api';

export async function listConversations(limit: number = 50, offset: number = 0): Promise<ConversationSummary[]> {
  return request<ConversationSummary[]>(`/api/v1/conversations?limit=${limit}&offset=${offset}`);
}

export async function getConversation(conversationId: string): Promise<ConversationSummary> {
  return request<ConversationSummary>(`/api/v1/conversations/${conversationId}`);
}

export async function getMessages(conversationId: string, limit: number = 50): Promise<ConversationHistoryResponse> {
  return request<ConversationHistoryResponse>(`/api/v1/conversations/${conversationId}/messages?limit=${limit}`);
}

export async function createConversation(title?: string): Promise<{ conversation_id: string; title: string }> {
  return request<{ conversation_id: string; title: string }>('/api/v1/conversations', {
    method: 'POST',
    body: JSON.stringify({ title }),
  });
}
