import React, { useState } from 'react';
import { SourceCitation } from '../../types/chat';

interface EvidenceAccordionProps {
  sources: SourceCitation[];
}

export const EvidenceAccordion: React.FC<EvidenceAccordionProps> = ({ sources }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-4 pt-3 border-t border-charcoal-100">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-xs font-medium text-charcoal-500 hover:text-charcoal-800 transition-colors group"
      >
        <svg
          className={`w-3.5 h-3.5 text-charcoal-400 group-hover:text-charcoal-600 transition-transform duration-200 ${
            isExpanded ? 'rotate-90 text-crimson-600' : ''
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7" />
        </svg>
        <span className="group-hover:underline">
          Sources & Remote-Sensing Evidence ({sources.length})
        </span>
      </button>

      {isExpanded && (
        <div className="mt-2.5 grid grid-cols-1 sm:grid-cols-2 gap-2.5 animate-fade-in">
          {sources.map((src) => {
            const stats = src.details?.statistics || src.details?.metrics || {};
            const statEntries = Object.entries(stats).slice(0, 4);

            return (
              <div
                key={src.id}
                className="p-3 rounded-xl bg-charcoal-50/80 border border-charcoal-200/60 text-xs"
              >
                <div className="flex items-center justify-between gap-2 mb-1">
                  <span className="font-semibold text-charcoal-800 text-[11px] uppercase tracking-wider">
                    {src.title}
                  </span>
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-mono bg-white text-charcoal-600 border border-charcoal-200/60">
                    {src.sensor || 'Sentinel'}
                  </span>
                </div>

                {src.resolution && (
                  <p className="text-[11px] text-charcoal-500 mb-1.5">
                    Spatial Resolution: <span className="text-charcoal-700 font-medium">{src.resolution}</span>
                  </p>
                )}

                {statEntries.length > 0 && (
                  <div className="mt-2 pt-1.5 border-t border-charcoal-200/40 grid grid-cols-2 gap-1 text-[10px]">
                    {statEntries.map(([key, val]) => (
                      <div key={key}>
                        <span className="text-charcoal-400 capitalize">{key.replace(/_/g, ' ')}: </span>
                        <span className="text-charcoal-700 font-mono font-medium">
                          {typeof val === 'number' ? (val % 1 !== 0 ? val.toFixed(3) : val) : String(val)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
