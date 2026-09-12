import { request } from './client';
import { ImageryItem, ImageryListResponse } from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export async function uploadImagery(file: File, sensor: string = 'Sentinel-2'): Promise<ImageryItem> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('sensor', sensor);

  const url = `${API_BASE_URL}/api/v1/imagery/upload`;
  const response = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.text();
    throw new Error(`Upload failed (${response.status}): ${err}`);
  }

  return response.json();
}

export async function listImagery(limit: number = 50, offset: number = 0): Promise<ImageryListResponse> {
  return request<ImageryListResponse>(`/api/v1/imagery?limit=${limit}&offset=${offset}`);
}

export async function getImagery(imageryId: string): Promise<ImageryItem> {
  return request<ImageryItem>(`/api/v1/imagery/${imageryId}`);
}

export function getImageryPreviewUrl(imageryId: string): string {
  return `${API_BASE_URL}/api/v1/imagery/${imageryId}/preview`;
}

export function getImageryFileUrl(imageryId: string): string {
  return `${API_BASE_URL}/api/v1/imagery/${imageryId}/file`;
}

