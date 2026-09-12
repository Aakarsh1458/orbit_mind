import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { useChatStore } from '../../store/useChatStore';

const MAP_STYLE = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';

export const MapDrawer: React.FC = () => {
  const { mapModalData, closeMapModal } = useChatStore();
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!mapModalData.isOpen || !mapContainerRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainerRef.current,
      style: MAP_STYLE,
      center: [0, 20],
      zoom: 2,
      attributionControl: false,
    });

    map.on('load', () => {
      // Add GeoJSON layer if available
      if (mapModalData.geojson) {
        map.addSource('analysis-data', {
          type: 'geojson',
          data: mapModalData.geojson,
        });

        // Fill layer
        map.addLayer({
          id: 'analysis-fill',
          type: 'fill',
          source: 'analysis-data',
          paint: {
            'fill-color': '#C1122F',
            'fill-opacity': 0.35,
          },
        });

        // Outline layer
        map.addLayer({
          id: 'analysis-line',
          type: 'line',
          source: 'analysis-data',
          paint: {
            'line-color': '#900C22',
            'line-width': 2,
          },
        });

        // Fit bounds
        const features = mapModalData.geojson.features || [];
        if (features.length > 0) {
          const bounds = new maplibregl.LngLatBounds();
          features.forEach((feat: any) => {
            const coords = feat.geometry?.coordinates;
            if (coords) {
              const flatten = (arr: any[]): any[] =>
                arr.length === 2 && typeof arr[0] === 'number'
                  ? [arr]
                  : arr.reduce((acc, val) => acc.concat(flatten(val)), []);
              flatten(coords).forEach((pt: any) => bounds.extend(pt));
            }
          });
          if (!bounds.isEmpty()) {
            map.fitBounds(bounds, { padding: 60, maxZoom: 14, duration: 1000 });
          }
        }
      }
    });

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [mapModalData.isOpen, mapModalData.geojson]);

  if (!mapModalData.isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-10 animate-fade-in">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-charcoal-950/40 backdrop-blur-sm"
        onClick={closeMapModal}
      />

      {/* Modal Container */}
      <div className="relative w-full max-w-5xl h-[85vh] bg-white rounded-3xl shadow-2xl border border-charcoal-200 overflow-hidden flex flex-col z-10 animate-slide-in">
        {/* Header */}
        <div className="px-6 py-4 border-b border-charcoal-100 flex items-center justify-between bg-white/90 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl bg-crimson-50 text-crimson-600 flex items-center justify-center border border-crimson-200/60">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-charcoal-900">
                {mapModalData.title || 'Satellite Geospatial Coverage'}
              </h3>
              <p className="text-[11px] text-charcoal-400">
                Vector boundaries & spatial polygon observations
              </p>
            </div>
          </div>

          <button
            onClick={closeMapModal}
            className="w-8 h-8 rounded-xl text-charcoal-400 hover:text-charcoal-700 hover:bg-charcoal-100 flex items-center justify-center transition"
            aria-label="Close map"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Map Canvas */}
        <div className="flex-1 relative w-full h-full bg-charcoal-50">
          <div ref={mapContainerRef} className="w-full h-full" />
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-charcoal-100 bg-charcoal-50/60 flex items-center justify-between text-xs text-charcoal-500">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-crimson-600" />
            <span>Active Analysis Boundaries (WGS84 EPSG:4326)</span>
          </div>
          <button
            onClick={closeMapModal}
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium bg-white hover:bg-charcoal-100 text-charcoal-700 border border-charcoal-200 transition"
          >
            Close Viewport
          </button>
        </div>
      </div>
    </div>
  );
};
