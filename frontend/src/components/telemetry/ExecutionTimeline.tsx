import React from 'react';
import { useOrbitStore } from '../../store/useOrbitStore';
import { Clock, CheckCircle, ArrowRight } from 'lucide-react';

export const ExecutionTimeline: React.FC = () => {
  const { executionSteps, isExecuting, currentResult } = useOrbitStore();

  if (executionSteps.length === 0 && !isExecuting) {
    return null;
  }

  return (
    <div className="bg-space-dark/95 border-t border-space-border px-4 py-2 font-mono text-xs select-none shadow-brutal-lg">
      <div className="flex items-center justify-between overflow-x-auto gap-4">
        <div className="flex items-center gap-2 shrink-0">
          <Clock className="w-3.5 h-3.5 text-electric-cyan" />
          <span className="font-bold uppercase tracking-wider text-slate-300 text-[11px]">
            MISSION TELEMETRY TIMELINE:
          </span>
        </div>

        {/* Step-by-step sequence */}
        <div className="flex items-center gap-2 overflow-x-auto text-[11px] shrink-0">
          {executionSteps.map((step, idx) => {
            const seconds = Math.floor(step.duration_ms / 1000);
            const ms = Math.floor((step.duration_ms % 1000) / 10);
            const timeStr = `00:${seconds.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;

            return (
              <React.Fragment key={idx}>
                <div
                  className={`flex items-center gap-1.5 px-2 py-1 border transition-colors ${
                    step.status === 'running'
                      ? 'bg-electric-violet/20 border-electric-violet text-white font-bold animate-pulse'
                      : 'bg-space-panel/60 border-space-border text-slate-300'
                  }`}
                >
                  <span className="text-electric-cyan text-[9px]">{timeStr}</span>
                  <span className="uppercase">{step.stage.replace('_', ' ')}</span>
                  {step.status === 'completed' && (
                    <CheckCircle className="w-3 h-3 text-radar-green" />
                  )}
                </div>
                {idx < executionSteps.length - 1 && (
                  <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Total latency pill */}
        {currentResult?.execution?.duration_ms && (
          <div className="shrink-0 pl-3 border-l border-space-border text-[10px] text-slate-400">
            TOTAL EXECUTION: <span className="text-radar-green font-bold">{currentResult.execution.duration_ms} ms</span>
          </div>
        )}
      </div>
    </div>
  );
};
