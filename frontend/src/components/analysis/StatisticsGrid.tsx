import React from 'react';
import { StatisticsData } from '../../types/orchestration';
import { BrutalistBadge } from '../brutalist/BrutalistBadge';

interface StatisticsGridProps {
  statistics?: StatisticsData;
  mode?: 'mock' | 'production';
}

export const StatisticsGrid: React.FC<StatisticsGridProps> = ({ statistics, mode }) => {
  if (!statistics || Object.keys(statistics).length === 0) {
    return (
      <div className="text-slate-400 font-mono text-xs p-3 text-center border border-space-border bg-space-dark">
        No numerical metrics generated for this task.
      </div>
    );
  }

  const items = [
    {
      label: 'CHANGED EXTENT',
      value:
        statistics.area_km2 !== undefined
          ? `${statistics.area_km2.toFixed(2)} km²`
          : 'N/A',
      sub:
        statistics.area_hectares !== undefined
          ? `${statistics.area_hectares.toFixed(1)} ha`
          : undefined,
      color: 'text-radar-green',
    },
    {
      label: 'CHANGE RATIO',
      value:
        statistics.change_percentage !== undefined
          ? `${statistics.change_percentage.toFixed(2)}%`
          : 'N/A',
      sub:
        statistics.changed_pixels !== undefined
          ? `${statistics.changed_pixels.toLocaleString()} px`
          : undefined,
      color: 'text-electric-cyan',
    },
    {
      label: 'PIXEL COVERAGE',
      value:
        statistics.total_pixels !== undefined
          ? statistics.total_pixels.toLocaleString()
          : 'N/A',
      sub: 'VALID SAMPLES',
      color: 'text-slate-200',
    },
  ];

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between font-mono text-[10px] text-slate-400 uppercase pb-1 border-b border-space-border">
        <span>SPATIAL QUANTIFICATION</span>
        <BrutalistBadge variant={mode === 'production' ? 'green' : 'amber'}>
          {mode === 'production' ? 'LIVE DATA' : 'MOCK CALIBRATION'}
        </BrutalistBadge>
      </div>

      <div className="grid grid-cols-3 gap-2">
        {items.map((it, idx) => (
          <div
            key={idx}
            className="bg-space-panel/90 border border-space-border p-2.5 flex flex-col justify-between font-mono shadow-brutal"
          >
            <span className="text-[9px] text-slate-400 tracking-wider uppercase font-semibold">
              {it.label}
            </span>
            <div className={`text-base font-bold my-1 ${it.color}`}>{it.value}</div>
            {it.sub && <span className="text-[9px] text-slate-400">// {it.sub}</span>}
          </div>
        ))}
      </div>
    </div>
  );
};
