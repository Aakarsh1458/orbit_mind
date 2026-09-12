import { request } from './client';
import { AIStatusResponse, HealthResponse, LLMProviderStatus, SpecialistModelDetail } from '../types/api';

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health');
}

export async function getAiStatus(): Promise<AIStatusResponse> {
  return request<AIStatusResponse>('/api/v1/ai/status');
}

export async function getModels(): Promise<SpecialistModelDetail[]> {
  return request<SpecialistModelDetail[]>('/api/v1/ai/models');
}

export async function getProviders(): Promise<LLMProviderStatus[]> {
  return request<LLMProviderStatus[]>('/api/v1/ai/providers');
}

export async function validateProvider(provider: string): Promise<any> {
  return request<any>(`/api/v1/ai/providers/${provider}/validate`, {
    method: 'POST',
  });
}
