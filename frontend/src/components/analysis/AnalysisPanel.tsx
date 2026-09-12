import React from 'react';
import { useOrbitStore } from '../../store/useOrbitStore';
import { StatisticsGrid } from './StatisticsGrid';
import { RoutingVisualizer } from './RoutingVisualizer';
import { BrutalistBadge } from '../brutalist/BrutalistBadge';
import { BrutalistButton } from '../brutalist/BrutalistButton';
import { Download, FileText, Activity, ShieldCheck } from 'lucide-react';
import { useMapStore } from '../../store/useMapStore';

export const AnalysisPanel: React.FC = () => {
  const { currentResult, isExecuting } = useOrbitStore();
  const { setActiveGeoJSON } = useMapStore();

  if (!currentResult && !isExecuting) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-6 text-center text-slate-500 font-mono text-xs select-none border border-space-border bg-space-card/90">
        <Activity className="w-8 h-8 text-slate-600 mb-2" />
        <div className="font-bold uppercase text-slate-400">NO ACTIVE ANALYSIS</div>
        <p className="text-[11px] text-slate-400 max-w-[240px] mt-1">
          Execute a query from the command console to display model evidence, spatial statistics, and routing telemetry.
        </p>
      </div>
    );
  }

  const analysis = currentResult?.analysis;
  const stats = currentResult?.statistics;
  const exec = currentResult?.execution;
  const isMock = stats?.mode === 'mock';

  return (
    <div className="h-full flex flex-col bg-space-card/90 border border-space-border overflow-y-auto p-3.5 space-y-3.5">
      {/* Top Header */}
      <div className="flex items-center justify-between pb-2 border-b border-space-border font-mono text-xs">
        <div className="flex items-center gap-2">
          <span className="font-bold uppercase text-slate-200">ANALYSIS SYNTHESIS</span>
          <BrutalistBadge variant={isMock ? 'amber' : 'green'}>
            {isMock ? 'CALIBRATION MODE' : 'OPERATIONAL'}
          </BrutalistBadge>
        </div>
        {exec?.duration_ms && (
          <span className="text-slate-400 text-[10px]">
            LATENCY: {exec.duration_ms} ms
          </span>
        )}
      </div>

      {/* Answer / Summary Text */}
      {currentResult?.answer && (
        <div className="bg-space-dark border border-space-border p-3 space-y-1.5">
          <span className="font-mono text-[10px] text-slate-400 uppercase font-semibold">
            FINDINGS & EXPLANATION:
          </span>
          <p className="text-sm font-sans text-slate-100 leading-relaxed">
            {currentResult.answer}
          </p>
        </div>
      )}

      {/* Numerical Spatial Metrics */}
      <StatisticsGrid statistics={stats} mode={isMock ? 'mock' : 'production'} />

      {/* Dynamic Model Routing Graph */}
      <RoutingVisualizer analysis={analysis} />

      {/* Action Buttons: Sync to Map and Artifacts */}
      {currentResult?.geojson && (
        <div className="pt-2 border-t border-space-border flex gap-2">
          <BrutalistButton
            variant="cyan"
            size="sm"
            className="w-full"
            onClick={() => setActiveGeoJSON(currentResult.geojson || null)}
          >
            FOCUS VECTOR ON MAP
          </BrutalistButton>
        </div>
      )}
    </div>
  );
};
