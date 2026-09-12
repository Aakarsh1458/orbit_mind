import React from 'react';

export const CosmicGrid: React.FC = () => {
  return (
    <div className="fixed inset-0 pointer-events-none z-0">
      {/* Corner Crosshairs */}
      <div className="absolute top-3 left-3 w-4 h-4 border-t border-l border-slate-700/80" />
      <div className="absolute top-3 right-3 w-4 h-4 border-t border-r border-slate-700/80" />
      <div className="absolute bottom-10 left-3 w-4 h-4 border-b border-l border-slate-700/80" />
      <div className="absolute bottom-10 right-3 w-4 h-4 border-b border-r border-slate-700/80" />

      {/* Perimeter Coordinates */}
      <div className="absolute top-2 left-10 font-mono text-[9px] text-slate-400 tracking-widest uppercase select-none">
        GRID // WGS84 // EPSG:4326
      </div>
      <div className="absolute top-2 right-10 font-mono text-[9px] text-slate-400 tracking-widest uppercase select-none hidden md:block">
        ORBIT // SUN-SYNCHRONOUS
      </div>
    </div>
  );
};
