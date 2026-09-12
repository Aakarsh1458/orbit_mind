import React from 'react';
import { useMapStore } from '../../store/useMapStore';
import { Plus, Minus, RotateCcw, SplitSquareVertical, Layers, Grid } from 'lucide-react';
import maplibregl from 'maplibre-gl';

interface MapControlsProps {
  mapRef: React.MutableRefObject<maplibregl.Map | null>;
}

export const MapControls: React.FC<MapControlsProps> = ({ mapRef }) => {
  const { activeLayers, toggleLayer, beforeAfter, toggleBeforeAfter, resetMap } = useMapStore();

  const handleZoomIn = () => {
    mapRef.current?.zoomIn();
  };

  const handleZoomOut = () => {
    mapRef.current?.zoomOut();
  };

  const handleReset = () => {
    resetMap();
    mapRef.current?.flyTo({
      center: [77.5946, 12.9716],
      zoom: 11,
      pitch: 0,
      bearing: 0,
      duration: 1200,
    });
  };

  return (
    <div className="absolute top-3 right-3 flex flex-col gap-1.5 z-20 font-mono text-xs select-none">
      {/* Zoom Controls */}
      <div className="bg-space-dark/95 border border-space-border flex flex-col p-0.5 shadow-brutal">
        <button
          onClick={handleZoomIn}
          className="p-2 hover:bg-space-panel text-slate-200 hover:text-white transition-colors"
          title="Zoom In"
        >
          <Plus className="w-3.5 h-3.5" />
        </button>
        <div className="h-px bg-space-border" />
        <button
          onClick={handleZoomOut}
          className="p-2 hover:bg-space-panel text-slate-200 hover:text-white transition-colors"
          title="Zoom Out"
        >
          <Minus className="w-3.5 h-3.5" />
        </button>
        <div className="h-px bg-space-border" />
        <button
          onClick={handleReset}
          className="p-2 hover:bg-space-panel text-slate-200 hover:text-white transition-colors"
          title="Reset Camera"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Layer and Mode Toggles */}
      <div className="bg-space-dark/95 border border-space-border flex flex-col p-0.5 shadow-brutal">
        <button
          onClick={toggleBeforeAfter}
          className={`p-2 transition-colors ${
            beforeAfter.enabled
              ? 'bg-electric-cyan text-space-black'
              : 'hover:bg-space-panel text-slate-300'
          }`}
          title="Toggle Bitemporal Comparison Slider (T1 vs T2)"
        >
          <SplitSquareVertical className="w-3.5 h-3.5" />
        </button>

        <div className="h-px bg-space-border" />

        <button
          onClick={() => toggleLayer('polygons')}
          className={`p-2 transition-colors ${
            activeLayers.polygons
              ? 'text-electric-violet bg-electric-violet/20'
              : 'text-slate-500 hover:bg-space-panel'
          }`}
          title="Toggle Analysis Vector Polygons"
        >
          <Layers className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
