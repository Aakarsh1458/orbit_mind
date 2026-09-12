import React from 'react';
import { EvidenceArtifact } from '../../types/orchestration';
import { FileText, Download, CheckCircle2, ShieldAlert } from 'lucide-react';
import { BrutalistBadge } from '../brutalist/BrutalistBadge';

interface EvidenceCardProps {
  evidence: EvidenceArtifact;
  index: number;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({ evidence, index }) => {
  const hasConfidence = evidence.confidence !== undefined && evidence.confidence !== null;

  return (
    <div className="bg-space-panel/90 border border-space-border p-3 font-mono text-xs space-y-2 shadow-brutal">
      <div className="flex items-center justify-between pb-1.5 border-b border-space-border text-[10px]">
        <div className="flex items-center gap-1.5">
          <span className="text-electric-violet font-bold">
            EVIDENCE // 0{index + 1}
          </span>
          <span className="text-slate-400 uppercase">// {evidence.type}</span>
        </div>

        <BrutalistBadge variant={hasConfidence ? 'green' : 'neutral'} size="sm">
          {hasConfidence
            ? `CONFIDENCE ${Math.round((evidence.confidence as number) * 100)}%`
            : 'CONFIDENCE N/A'}
        </BrutalistBadge>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[10px]">
        <div>
          <span className="text-slate-400 block uppercase text-[9px]">SOURCE SENSOR:</span>
          <span className="text-slate-200 font-bold">{evidence.source || 'SENTINEL-2'}</span>
        </div>

        {evidence.area_km2 !== undefined && (
          <div>
            <span className="text-slate-400 block uppercase text-[9px]">QUANTIFIED EXTENT:</span>
            <span className="text-radar-green font-bold">{evidence.area_km2.toFixed(2)} km²</span>
          </div>
        )}

        {evidence.path && (
          <div className="col-span-2">
            <span className="text-slate-400 block uppercase text-[9px]">OUTPUT GEOTIFF:</span>
            <span className="text-electric-cyan font-bold truncate block">
              {evidence.path}
            </span>
          </div>
        )}
      </div>

      {evidence.description && (
        <p className="text-[11px] font-sans text-slate-300 pt-1 border-t border-space-border">
          {evidence.description}
        </p>
      )}
    </div>
  );
};
