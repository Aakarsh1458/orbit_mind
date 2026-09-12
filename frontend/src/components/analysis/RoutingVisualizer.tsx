import React from 'react';
import { ArrowRight, Cpu, Network, CheckCircle2 } from 'lucide-react';
import { AnalysisMetadata } from '../../types/orchestration';

interface RoutingVisualizerProps {
  analysis?: AnalysisMetadata;
}

const MODELS = [
  { id: 'change_detection_v1', task: 'change_detection', label: 'CHANGE DETECTION' },
  { id: 'segmentation_v1', task: 'segmentation', label: 'SEGMENTATION' },
  { id: 'vqa_v1', task: 'vqa', label: 'VQA SPECIALIST' },
  { id: 'captioning_v1', task: 'captioning', label: 'SCENE CAPTION' },
  { id: 'optical_sar_v1', task: 'optical_sar', label: 'OPTICAL + SAR' },
];

export const RoutingVisualizer: React.FC<RoutingVisualizerProps> = ({ analysis }) => {
  const currentTask = analysis?.task;
  const currentModel = analysis?.model;

  return (
    <div className="bg-space-dark border border-space-border p-3 space-y-2.5 font-mono text-xs select-none">
      <div className="flex items-center justify-between pb-1.5 border-b border-space-border text-[10px] text-slate-400 uppercase">
        <span className="flex items-center gap-1.5 text-slate-300 font-bold">
          <Network className="w-3.5 h-3.5 text-electric-cyan" />
          MODEL ROUTING ARCHITECTURE
        </span>
        <span>{analysis?.fallback_used ? 'FALLBACK ACTIVE' : 'OPTIMAL ROUTE'}</span>
      </div>

      <div className="flex items-center justify-between gap-1 text-[10px]">
        {/* Step 1: Query Input */}
        <div className="bg-space-panel border border-space-border p-2 text-center flex-1">
          <span className="text-slate-400 block text-[8px] uppercase">STAGE 01</span>
          <span className="text-slate-200 font-bold">USER QUERY</span>
        </div>

        <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />

        {/* Step 2: Intent Classification */}
        <div className="bg-space-panel border border-space-border p-2 text-center flex-1">
          <span className="text-slate-400 block text-[8px] uppercase">STAGE 02</span>
          <span className="text-electric-cyan font-bold">
            {currentTask ? currentTask.toUpperCase() : 'CLASSIFYING'}
          </span>
        </div>

        <ArrowRight className="w-3 h-3 text-slate-600 shrink-0" />

        {/* Step 3: Model Execution */}
        <div
          className={`border p-2 text-center flex-1 ${
            currentModel
              ? 'bg-electric-violet/20 border-electric-violet text-white font-bold'
              : 'bg-space-panel border-space-border text-slate-400'
          }`}
        >
          <span className="text-slate-400 block text-[8px] uppercase">STAGE 03</span>
          <span className="text-electric-violet font-bold">
            {currentModel ? currentModel.toUpperCase() : 'MODEL ROUTER'}
          </span>
        </div>
      </div>

      {/* Specialist Model Matrix */}
      <div className="pt-2 border-t border-space-border">
        <span className="text-[9px] text-slate-400 uppercase block mb-1.5">
          AVAILABLE SPECIALISTS:
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-1.5 text-[10px]">
          {MODELS.map((m) => {
            const isRouted = currentTask === m.task || currentModel === m.id;
            return (
              <div
                key={m.id}
                className={`p-1.5 border flex items-center justify-between transition-colors ${
                  isRouted
                    ? 'bg-electric-violet/20 border-electric-violet text-white font-bold'
                    : 'bg-space-panel/40 border-space-border text-slate-400'
                }`}
              >
                <span className="truncate">{m.label}</span>
                {isRouted && <CheckCircle2 className="w-3 h-3 text-radar-green shrink-0 ml-1" />}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
