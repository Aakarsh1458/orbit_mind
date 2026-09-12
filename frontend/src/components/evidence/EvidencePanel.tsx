import React from 'react';
import { useOrbitStore } from '../../store/useOrbitStore';
import { EvidenceCard } from './EvidenceCard';
import { ShieldCheck, Layers, FileDown } from 'lucide-react';
import { getDownloadUrl } from '../../api/analysisApi';

export const EvidencePanel: React.FC = () => {
  const { currentResult } = useOrbitStore();

  const evidenceItems = currentResult?.evidence || [];
  const artifacts = currentResult?.artifacts || [];

  return (
    <div className="space-y-3 font-mono text-xs">
      <div className="flex items-center justify-between pb-1.5 border-b border-space-border">
        <span className="font-bold uppercase tracking-wider text-slate-200 flex items-center gap-1.5">
          <ShieldCheck className="w-3.5 h-3.5 text-radar-green" />
          FACTUAL EVIDENCE ARTIFACTS ({evidenceItems.length})
        </span>
        <span className="text-[10px] text-slate-400">GROUND TRUTH VALIDATED</span>
      </div>

      {evidenceItems.length === 0 ? (
        <div className="text-slate-400 text-[11px] p-3 border border-space-border bg-space-dark text-center">
          No separate evidence items returned for this inference run.
        </div>
      ) : (
        <div className="space-y-2">
          {evidenceItems.map((item, idx) => (
            <EvidenceCard key={idx} evidence={item} index={idx} />
          ))}
        </div>
      )}

      {/* Generated GeoTIFF Mask Files */}
      {artifacts.length > 0 && (
        <div className="mt-3 pt-2.5 border-t border-space-border space-y-1.5">
          <span className="text-[10px] text-slate-400 uppercase font-semibold block">
            DOWNLOADABLE GEOTIFF RASTERS:
          </span>
          {artifacts.map((art, i) => (
            <div
              key={i}
              className="flex items-center justify-between p-2 bg-space-dark border border-space-border hover:border-electric-cyan transition-colors"
            >
              <div className="truncate text-[11px] text-slate-200">
                <span>{art.name}</span>
                <span className="text-slate-400 text-[9px] ml-2">// {art.type}</span>
              </div>
              {currentResult?.request_id && (
                <a
                  href={getDownloadUrl(currentResult.request_id, art.name)}
                  target="_blank"
                  rel="noreferrer"
                  className="px-2 py-0.5 bg-electric-cyan/20 border border-electric-cyan text-electric-cyan text-[10px] font-bold uppercase hover:bg-electric-cyan hover:text-space-black transition-colors"
                >
                  DOWNLOAD
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
