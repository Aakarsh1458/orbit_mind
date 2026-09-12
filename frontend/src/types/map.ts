export interface ViewportState {
  longitude: number;
  latitude: number;
  zoom: number;
  bearing?: number;
  pitch?: number;
}

export interface MapLayerConfig {
  id: string;
  label: string;
  type: 'vector' | 'raster' | 'geojson';
  visible: boolean;
  opacity: number;
  color?: string;
}

export interface BoundingBox {
  minx: number;
  miny: number;
  maxx: number;
  maxy: number;
}

export interface BeforeAfterConfig {
  enabled: boolean;
  sliderPosition: number; // 0 to 100 percentage
  beforeLabel: string;
  afterLabel: string;
}
