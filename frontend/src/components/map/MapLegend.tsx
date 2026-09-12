import React, { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';

export const MapLegend: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className="absolute bottom-4 right-3 bg-space-dark/95 border border-space-border p-2.5 z-20 font-mono text-xs shadow-brutal select-none max-w-[200px] backdrop-blur-sm">
      <div
        className="flex items-center justify-between cursor-pointer pb-1 border-b border-space-border"
        onClick={() => setCollapsed(!collapsed)}
      >
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-300">
          MAP LEGEND
        </span>
        {collapsed ? (
          <ChevronUp className="w-3 h-3 text-slate-400" />
        ) : (
          <ChevronDown className="w-3 h-3 text-slate-400" />
        )}
      </div>

      {!collapsed && (
        <div className="space-y-1.5 pt-2 text-[10px]">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-electric-violet/50 border border-electric-cyan" />
            <span className="text-slate-300">DETECTED CHANGE</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-radar-green/50 border border-radar-green" />
            <span className="text-slate-300">VEGETATION</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-electric-cyan/40 border border-electric-cyan" />
            <span className="text-slate-300">WATER BODY</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 bg-space-dark border border-slate-600" />
            <span className="text-slate-400">UNCHANGED BASE</span>
          </div>
        </div>
      )}
    </div>
  );
};
