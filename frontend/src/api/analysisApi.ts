import { request } from './client';
import { AnalysisJobItem, AnalysisResultResponse } from '../types/api';

export interface StartAnalysisPayload {
  query?: string;
  imagery_ids: string[];
  analysis_type?: string;
}

export async function startAnalysis(payload: StartAnalysisPayload): Promise<{ job_id: string; status: string }> {
  return request<{ job_id: string; status: string }>('/api/v1/analysis', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getJobStatus(jobId: string): Promise<AnalysisJobItem> {
  return request<AnalysisJobItem>(`/api/v1/jobs/${jobId}`);
}

export async function listJobs(limit: number = 50, offset: number = 0): Promise<AnalysisJobItem[]> {
  return request<AnalysisJobItem[]>(`/api/v1/jobs?limit=${limit}&offset=${offset}`);
}

export async function getAnalysisResult(jobId: string): Promise<AnalysisResultResponse> {
  return request<AnalysisResultResponse>(`/api/v1/results/${jobId}`);
}

export function getDownloadUrl(jobId: string, filename: string): string {
  const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
  return `${API_BASE_URL}/api/v1/results/${jobId}/download/${filename}`;
}
