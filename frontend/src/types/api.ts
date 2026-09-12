export interface HealthResponse {
  status: string;
  app_env: string;
  version: string;
  ai_mode: string;
  device: string;
  database: string;
}

export interface AIStatusResponse {
  ai_mode: 'mock' | 'production';
  llm: {
    default_provider: string;
    status: 'configured' | 'unconfigured';
  };
  device: string;
  specialist_models: {
    vqa?: string;
    captioning?: string;
    change_detection?: string;
    segmentation?: string;
    optical_sar?: string;
    [key: string]: string | undefined;
  };
}

export interface SpecialistModelDetail {
  id: string;
  task: string;
  capabilities: {
    task: string;
    modalities: string[];
    min_rasters: number;
    max_rasters: number;
    description: string;
    supported_formats: string[];
    requires_alignment: boolean;
  };
  supported_modes: string[];
  loaded: boolean;
  fallback_model_id?: string | null;
}

export interface LLMProviderStatus {
  provider: string;
  configured: boolean;
  is_default: boolean;
}

export interface ImageryItem {
  id: string;
  filename: string;
  file_path: string;
  file_size_bytes: number;
  format: string;
  sensor?: string;
  width?: number;
  height?: number;
  crs?: string;
  bounds?: [number, number, number, number]; // [minx, miny, maxx, maxy]
  resolution_meters?: number;
  uploaded_at: string;
}

export interface ImageryListResponse {
  total: number;
  items: ImageryItem[];
}

export interface ConversationSummary {
  conversation_id: string;
  title: string;
  metadata?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessageItem {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  imagery_ids?: string[];
  task?: string;
  created_at: string;
}

export interface ConversationHistoryResponse {
  conversation_id: string;
  total_messages: number;
  messages: ConversationMessageItem[];
}

export interface AnalysisJobItem {
  job_id: string;
  query?: string;
  analysis_type: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  error?: string | null;
}

export interface AnalysisResultResponse {
  job_id: string;
  analysis_type: string;
  mode: 'mock' | 'production';
  summary: string;
  confidence?: number | null;
  statistics: Record<string, any>;
  evidence: Record<string, any>;
  execution_trace: string[];
  created_at: string;
}
