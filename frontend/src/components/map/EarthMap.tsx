import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import { useMapStore } from '../../store/useMapStore';
import { MapControls } from './MapControls';
import { MapLegend } from './MapLegend';
import { BeforeAfterSlider } from './BeforeAfterSlider';

// Free high-contrast dark satellite/vector style (CartoDB Dark Matter)
const DARK_STYLE_URL = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';

export const EarthMap: React.FC = () => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const { viewport, setViewport, setCursorCoordinates, activeGeoJSON, activeLayers, beforeAfter } =
    useMapStore();

  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: DARK_STYLE_URL,
      center: [viewport.longitude, viewport.latitude],
      zoom: viewport.zoom,
      bearing: viewport.bearing || 0,
      pitch: viewport.pitch || 0,
      attributionControl: false,
    });

    map.on('move', () => {
      const center = map.getCenter();
      setViewport({
        longitude: center.lng,
        latitude: center.lat,
        zoom: map.getZoom(),
      });
    });

    map.on('mousemove', (e) => {
      setCursorCoordinates([e.lngLat.lng, e.lngLat.lat]);
    });

    map.on('load', () => {
      // Add empty GeoJSON source for analysis vectors
      map.addSource('analysis-vectors', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [],
        },
      });

      // Polygon fill layer with electric violet / cyan highlight
      map.addLayer({
        id: 'analysis-polygons-fill',
        type: 'fill',
        source: 'analysis-vectors',
        paint: {
          'fill-color': '#8b5cf6',
          'fill-opacity': 0.45,
        },
      });

      // Polygon outline border
      map.addLayer({
        id: 'analysis-polygons-outline',
        type: 'line',
        source: 'analysis-vectors',
        paint: {
          'line-color': '#06b6d4',
          'line-width': 2.5,
          'line-dasharray': [2, 1],
        },
      });
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update GeoJSON source and fit bounds when analysis vector changes
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const source = map.getSource('analysis-vectors') as maplibregl.GeoJSONSource | undefined;
    if (source && activeGeoJSON) {
      source.setData(activeGeoJSON as any);

      // Auto-fit bounds if features exist
      if (activeGeoJSON.features && activeGeoJSON.features.length > 0) {
        const bounds = new maplibregl.LngLatBounds();
        activeGeoJSON.features.forEach((feat: any) => {
          if (feat.geometry?.coordinates) {
            const coords = feat.geometry.coordinates;
            const flatten = (arr: any[]): any[] =>
              arr.length === 2 && typeof arr[0] === 'number'
                ? [arr]
                : arr.reduce((acc, val) => acc.concat(flatten(val)), []);
            const allPoints = flatten(coords);
            allPoints.forEach((pt: any) => bounds.extend(pt));
          }
        });
        if (!bounds.isEmpty()) {
          map.fitBounds(bounds, { padding: 80, maxZoom: 14, duration: 1500 });
        }
      }
    }
  }, [activeGeoJSON]);

  // Handle Layer Visibility
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !map.isStyleLoaded()) return;

    const fillVis = activeLayers.polygons ? 'visible' : 'none';
    if (map.getLayer('analysis-polygons-fill')) {
      map.setLayoutProperty('analysis-polygons-fill', 'visibility', fillVis);
    }
    if (map.getLayer('analysis-polygons-outline')) {
      map.setLayoutProperty('analysis-polygons-outline', 'visibility', fillVis);
    }
  }, [activeLayers]);

  return (
    <div className="relative w-full h-full min-h-[400px] border border-space-border bg-space-black overflow-hidden select-none">
      {/* MapLibre WebGL Viewport */}
      <div ref={mapContainerRef} className="w-full h-full" />

      {/* Before / After Split Slider Overlay if enabled */}
      {beforeAfter.enabled && <BeforeAfterSlider />}

      {/* Floating Tactical Overlay Crosshairs */}
      <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
        <div className="w-6 h-6 border-t border-b border-electric-cyan/40" />
        <div className="w-6 h-6 border-l border-r border-electric-cyan/40 -ml-6" />
      </div>

      {/* Map Controls */}
      <MapControls mapRef={mapRef} />

      {/* Map Legend */}
      <MapLegend />

      {/* Corner Metadata Box */}
      <div className="absolute top-3 left-3 bg-space-dark/90 border border-space-border px-2.5 py-1.5 font-mono text-[10px] text-slate-300 pointer-events-none backdrop-blur-sm">
        <div className="flex items-center gap-1.5 text-electric-cyan font-bold">
          <span className="w-1.5 h-1.5 bg-electric-cyan animate-pulse" />
          <span>EARTH OBSERVATION VIEWPORT</span>
        </div>
        <div className="text-slate-400 mt-0.5">
          PROJECTION: EPSG:4326 // SATELLITE TILES ACTIVE
        </div>
      </div>
    </div>
  );
};
