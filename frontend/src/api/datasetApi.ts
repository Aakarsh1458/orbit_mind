import { request } from './client';

export interface RegisteredSampleImagery {
  id: string;
  type: string;
  filename: string;
  sensor: string;
}

export interface LoadSampleResponse {
  sample_idx: number;
  season?: string;
  scene?: string;
  optical_imagery_id: string;
  target_imagery_id: string;
  sar_imagery_id: string;
  imagery_ids: string[];
  files?: {
    optical: string;
    target: string;
    sar: string;
  };
}

export async function listDatasetSamples(limit: number = 10): Promise<any[]> {
  return request<any[]>(`/api/v1/dataset/samples?limit=${limit}`);
}

export async function loadDatasetSample(sampleIdx: number = 0): Promise<LoadSampleResponse> {
  return request<LoadSampleResponse>(`/api/v1/dataset/load-sample/${sampleIdx}`, {
    method: 'POST',
  });
}
