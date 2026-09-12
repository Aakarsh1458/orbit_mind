export type OrchestrationStage =
  | 'planning'
  | 'model_selection'
  | 'preprocessing'
  | 'inference'
  | 'validation'
  | 'evidence_generation'
  | 'response_generation'
  | 'completed'
  | 'failed';

export interface OrchestrationStep {
  step: number;
  stage: OrchestrationStage | string;
  action: string;
  status: 'completed' | 'failed' | 'running' | 'pending';
  duration_ms: number;
}

export interface EvidenceArtifact {
  id?: string;
  type: string;
  source?: string;
  path?: string;
  paths?: string[];
  value?: number;
  confidence?: number;
  area_km2?: number;
  coordinates?: [number, number];
  description?: string;
  metrics?: Record<string, any>;
}

export interface AnalysisMetadata {
  task?: string;
  model?: string;
  fallback_used?: boolean;
  provider?: string;
}

export interface ExecutionMetadata {
  steps: number;
  duration_ms: number;
  trace: string[];
}

export interface StatisticsData {
  changed_pixels?: number;
  total_pixels?: number;
  change_percentage?: number;
  area_km2?: number;
  area_hectares?: number;
  classes?: Record<string, number>;
  mode?: 'mock' | 'production';
  [key: string]: any;
}

export interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: 'Polygon' | 'MultiPolygon' | 'Point' | 'LineString';
    coordinates: any;
  };
  properties: Record<string, any>;
}

export interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}

export interface ChatResponse {
  request_id: string;
  conversation_id: string;
  status: 'completed' | 'failed' | 'needs_input' | 'initialized' | string;
  answer?: string | null;
  analysis?: AnalysisMetadata;
  statistics?: StatisticsData;
  evidence?: EvidenceArtifact[];
  geojson?: GeoJSONFeatureCollection | null;
  artifacts?: Array<{
    name: string;
    path: string;
    type: string;
  }>;
  execution?: ExecutionMetadata;
  follow_up_suggestions?: string[];
  errors?: string[] | null;
}

export interface SSEEvent {
  event: 'status' | 'completed' | 'failed' | 'message';
  data: {
    stage?: OrchestrationStage;
    [key: string]: any;
  };
}
