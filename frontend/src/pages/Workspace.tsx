import React, { useState } from 'react';
import { ChatPanel } from '../components/chat/ChatPanel';
import { SatelliteImageViewport } from '../components/map/SatelliteImageViewport';
import { AnalysisPanel } from '../components/analysis/AnalysisPanel';
import { EvidencePanel } from '../components/evidence/EvidencePanel';
import { ExecutionTimeline } from '../components/telemetry/ExecutionTimeline';
import { Terminal, Image as ImageIcon, Activity, ShieldCheck, ChevronRight } from 'lucide-react';

export const Workspace: React.FC = () => {
  // Mobile / Tablet Tab Switcher
  const [activeMobileTab, setActiveMobileTab] = useState<'chat' | 'image' | 'analysis' | 'evidence'>(
    'image'
  );
  const [rightTab, setRightTab] = useState<'analysis' | 'evidence'>('analysis');

  return (
    <div className="relative z-10 flex flex-col h-[calc(100vh-45px-32px)] overflow-hidden">
      {/* Mobile Top Tab Bar (Hidden on lg screens) */}
      <div className="lg:hidden flex items-center justify-around bg-space-dark border-b border-space-border p-1.5 font-mono text-xs select-none">
        <button
          onClick={() => setActiveMobileTab('image')}
          className={`px-3 py-1.5 border flex items-center gap-1.5 ${
            activeMobileTab === 'image'
              ? 'bg-space-panel border-electric-cyan text-electric-cyan font-bold'
              : 'border-transparent text-slate-400'
          }`}
        >
          <ImageIcon className="w-3.5 h-3.5" />
          <span>IMAGE</span>
        </button>

        <button
          onClick={() => setActiveMobileTab('chat')}
          className={`px-3 py-1.5 border flex items-center gap-1.5 ${
            activeMobileTab === 'chat'
              ? 'bg-space-panel border-electric-violet text-electric-violet font-bold'
              : 'border-transparent text-slate-400'
          }`}
        >
          <Terminal className="w-3.5 h-3.5" />
          <span>CHAT / AI</span>
        </button>

        <button
          onClick={() => setActiveMobileTab('analysis')}
          className={`px-3 py-1.5 border flex items-center gap-1.5 ${
            activeMobileTab === 'analysis'
              ? 'bg-space-panel border-radar-green text-radar-green font-bold'
              : 'border-transparent text-slate-400'
          }`}
        >
          <Activity className="w-3.5 h-3.5" />
          <span>ANALYSIS</span>
        </button>

        <button
          onClick={() => setActiveMobileTab('evidence')}
          className={`px-3 py-1.5 border flex items-center gap-1.5 ${
            activeMobileTab === 'evidence'
              ? 'bg-space-panel border-slate-300 text-slate-200 font-bold'
              : 'border-transparent text-slate-400'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>EVIDENCE</span>
        </button>
      </div>

      {/* Main 3-Column Layout on Desktop */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 overflow-hidden">
        {/* Left Column: AI Chat Command Console (Width: 3.5 cols on desktop) */}
        <div
          className={`h-full lg:col-span-4 xl:col-span-3 lg:block overflow-hidden ${
            activeMobileTab === 'chat' ? 'block' : 'hidden'
          }`}
        >
          <ChatPanel />
        </div>

        {/* Center Column: Satellite Image Viewport (Width: 5 cols on desktop) */}
        <div
          className={`h-full lg:col-span-4 xl:col-span-5 relative lg:block overflow-hidden ${
            activeMobileTab === 'image' ? 'block' : 'hidden'
          }`}
        >
          <SatelliteImageViewport />
        </div>

        {/* Right Column: Analysis & Evidence (Width: 4.5 cols on desktop) */}
        <div
          className={`h-full lg:col-span-4 xl:col-span-4 flex flex-col bg-space-card/95 border-l border-space-border lg:block overflow-hidden ${
            activeMobileTab === 'analysis' || activeMobileTab === 'evidence' ? 'block' : 'hidden'
          }`}
        >
          {/* Sub-tab switcher: Analysis vs Evidence */}
          <div className="flex items-center border-b border-space-border bg-space-panel/90 px-3 py-1.5 font-mono text-xs select-none">
            <button
              onClick={() => setRightTab('analysis')}
              className={`px-3 py-1 border transition-colors ${
                rightTab === 'analysis'
                  ? 'bg-space-dark border-electric-cyan text-electric-cyan font-bold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              SYNTHESIS & ROUTING
            </button>

            <button
              onClick={() => setRightTab('evidence')}
              className={`px-3 py-1 border transition-colors ml-2 ${
                rightTab === 'evidence'
                  ? 'bg-space-dark border-radar-green text-radar-green font-bold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              GROUND EVIDENCE
            </button>
          </div>

          <div className="flex-1 overflow-y-auto">
            {rightTab === 'analysis' ? <AnalysisPanel /> : <div className="p-3"><EvidencePanel /></div>}
          </div>
        </div>
      </div>

      {/* Bottom Mission Telemetry Timeline */}
      <ExecutionTimeline />
    </div>
  );
};
