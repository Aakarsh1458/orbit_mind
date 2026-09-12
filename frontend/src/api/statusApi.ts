import { request } from './client';

export interface SystemStatus {
  available: boolean;
  statusText: string;
}

export async function checkAiAvailability(): Promise<SystemStatus> {
  try {
    const res = await request<any>('/api/v1/ai/status');
    return {
      available: true,
      statusText: 'OrbitMind is online and operational.'
    };
  } catch (err: any) {
    return {
      available: false,
      statusText: 'OrbitMind AI is temporarily unavailable.'
    };
  }
}
