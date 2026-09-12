import { create } from 'zustand';
import { BeforeAfterConfig, ViewportState } from '../types/map';
import { GeoJSONFeatureCollection } from '../types/orchestration';

interface MapStoreState {
  viewport: ViewportState;
  activeLayers: {
    polygons: boolean;
    changeMask: boolean;
    grid: boolean;
    satellites: boolean;
    labels: boolean;
  };
  beforeAfter: BeforeAfterConfig;
  activeGeoJSON: GeoJSONFeatureCollection | null;
  cursorCoordinates: [number, number] | null;

  // Actions
  setViewport: (viewport: Partial<ViewportState>) => void;
  toggleLayer: (layerName: keyof MapStoreState['activeLayers']) => void;
  setBeforeAfterSlider: (position: number) => void;
  toggleBeforeAfter: () => void;
  setActiveGeoJSON: (geojson: GeoJSONFeatureCollection | null) => void;
  setCursorCoordinates: (coords: [number, number] | null) => void;
  resetMap: () => void;
}

const DEFAULT_VIEWPORT: ViewportState = {
  longitude: 77.5946,
  latitude: 12.9716,
  zoom: 11,
  bearing: 0,
  pitch: 0,
};

export const useMapStore = create<MapStoreState>((set) => ({
  viewport: DEFAULT_VIEWPORT,
  activeLayers: {
    polygons: true,
    changeMask: true,
    grid: true,
    satellites: true,
    labels: true,
  },
  beforeAfter: {
    enabled: false,
    sliderPosition: 50,
    beforeLabel: '2022 BASELINE (T1)',
    afterLabel: '2025 ACQUISITION (T2)',
  },
  activeGeoJSON: null,
  cursorCoordinates: [77.5946, 12.9716],

  setViewport: (vp) =>
    set((state) => ({ viewport: { ...state.viewport, ...vp } })),

  toggleLayer: (layerName) =>
    set((state) => ({
      activeLayers: {
        ...state.activeLayers,
        [layerName]: !state.activeLayers[layerName],
      },
    })),

  setBeforeAfterSlider: (position) =>
    set((state) => ({
      beforeAfter: { ...state.beforeAfter, sliderPosition: position },
    })),

  toggleBeforeAfter: () =>
    set((state) => ({
      beforeAfter: {
        ...state.beforeAfter,
        enabled: !state.beforeAfter.enabled,
      },
    })),

  setActiveGeoJSON: (geojson) => set({ activeGeoJSON: geojson }),
  setCursorCoordinates: (coords) => set({ cursorCoordinates: coords }),
  resetMap: () => set({ viewport: DEFAULT_VIEWPORT }),
}));
