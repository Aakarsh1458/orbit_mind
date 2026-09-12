import { request } from './client';
import { ChatResponse, OrchestrationStage } from '../types/orchestration';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export interface ChatPayload {
  message: string;
  conversation_id?: string | null;
  imagery_ids?: string[];
}

export async function sendChat(payload: ChatPayload): Promise<ChatResponse> {
  return request<ChatResponse>('/api/v1/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export interface StreamCallbacks {
  onStatus?: (stage: OrchestrationStage, data: any) => void;
  onCompleted?: (result: ChatResponse) => void;
  onFailed?: (error: any) => void;
  onError?: (err: Error) => void;
}

export async function streamChat(
  payload: ChatPayload,
  callbacks: StreamCallbacks,
  signal?: AbortSignal
): Promise<void> {
  const url = `${API_BASE_URL}/api/v1/chat/stream`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      signal,
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`SSE request failed (${response.status}): ${errText}`);
    }

    if (!response.body) {
      throw new Error('ReadableStream not supported by browser.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
      buffer = events.pop() || ''; // Keep partial chunk

      for (const eventBlock of events) {
        if (!eventBlock.trim()) continue;

        let eventName = 'message';
        let dataStr = '';

        const lines = eventBlock.split('\n');
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventName = line.substring(7).trim();
          } else if (line.startsWith('data: ')) {
            dataStr = line.substring(6).trim();
          }
        }

        if (!dataStr) continue;

        try {
          const parsedData = JSON.parse(dataStr);
          if (eventName === 'status') {
            callbacks.onStatus?.(parsedData.stage, parsedData);
          } else if (eventName === 'completed' || eventName === 'needs_input') {
            callbacks.onCompleted?.(parsedData as ChatResponse);
          } else if (eventName === 'failed') {
            callbacks.onFailed?.(parsedData);
          }
        } catch (parseErr) {
          console.warn('Failed to parse SSE JSON:', dataStr, parseErr);
        }
      }
    }
  } catch (err: any) {
    if (err.name !== 'AbortError') {
      callbacks.onError?.(err);
    }
  }
}
