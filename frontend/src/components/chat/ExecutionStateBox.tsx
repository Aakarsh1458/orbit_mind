import React from 'react';
import { useOrbitStore } from '../../store/useOrbitStore';
import { OrchestrationStage } from '../../types/orchestration';
import { Check, Loader2, Circle, AlertTriangle } from 'lucide-react';

const STAGES: { key: OrchestrationStage; label: string }[] = [
  { key: 'planning', label: 'TASK PLANNING & INTENT' },
  { key: 'model_selection', label: 'MODEL ROUTER' },
  { key: 'preprocessing', label: 'GEOSPATIAL ALIGNMENT' },
  { key: 'inference', label: 'REMOTE SENSING INFERENCE' },
  { key: 'validation', label: 'OUTPUT VALIDATION' },
  { key: 'response_generation', label: 'EVIDENCE & SYNTHESIS' },
];

export const ExecutionStateBox: React.FC = () => {
  const { isExecuting, activeStage, executionSteps, lastError } = useOrbitStore();

  if (!isExecuting && executionSteps.length === 0 && !lastError) {
    return null;
  }

  const currentStageIndex = STAGES.findIndex((s) => s.key === activeStage);

  return (
    <div className="bg-space-dark/95 border border-space-border p-3.5 my-3 select-none">
      <div className="flex items-center justify-between pb-2 mb-2.5 border-b border-space-border">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-electric-violet animate-ping" />
          <span className="font-mono text-xs uppercase font-bold text-slate-200">
            ORBITMIND EXECUTION ENGINE
          </span>
        </div>
        <span className="font-mono text-[10px] text-electric-cyan">
          {isExecuting ? 'ACTIVE' : lastError ? 'HALTED' : 'DONE'}
        </span>
      </div>

      {lastError ? (
        <div className="flex items-start gap-2 p-2.5 bg-radar-red/10 border border-radar-red/40 text-radar-red font-mono text-xs">
          <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>
            <div className="font-bold">EXECUTION ERROR</div>
            <div className="text-[11px] text-slate-300 mt-0.5">{lastError}</div>
          </div>
        </div>
      ) : (
        <div className="space-y-1.5 font-mono text-[11px]">
          {STAGES.map((stg, idx) => {
            const isDone = currentStageIndex > idx || activeStage === 'completed';
            const isCurrent = activeStage === stg.key;
            const isPending = currentStageIndex < idx && activeStage !== 'completed';

            return (
              <div
                key={stg.key}
                className={`flex items-center justify-between px-2 py-1 border transition-colors ${
                  isCurrent
                    ? 'bg-electric-violet/15 border-electric-violet text-white font-bold'
                    : isDone
                    ? 'bg-space-panel/40 border-space-border text-slate-300'
                    : 'bg-transparent border-transparent text-slate-600'
                }`}
              >
                <div className="flex items-center gap-2">
                  {isDone ? (
                    <Check className="w-3.5 h-3.5 text-radar-green" />
                  ) : isCurrent ? (
                    <Loader2 className="w-3.5 h-3.5 text-electric-cyan animate-spin" />
                  ) : (
                    <Circle className="w-3 h-3 text-slate-600" />
                  )}
                  <span>{stg.label}</span>
                </div>

                <span className="text-[10px] text-slate-400">
                  {isDone ? 'PASS' : isCurrent ? 'RUNNING' : 'WAIT'}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
