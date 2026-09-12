import React from 'react';
import { useOrbitStore } from '../../store/useOrbitStore';
import { useMapStore } from '../../store/useMapStore';
import { Radio, Database, Cpu, Activity, Compass } from 'lucide-react';

export const SystemStatusBar: React.FC = () => {
  const { health, aiStatus } = useOrbitStore();
  const { cursorCoordinates, viewport } = useMapStore();

  const isApiOnline = Boolean(health?.status === 'ok' || health?.status === 'healthy');
  const isAiOnline = Boolean(aiStatus?.llm?.status === 'configured');

  return (
    <footer className="fixed bottom-0 left-0 right-0 z-30 bg-space-dark/95 backdrop-blur-md border-t border-space-border px-3 py-1.5 font-mono text-[11px] text-slate-400 select-none">
      <div className="flex items-center justify-between overflow-x-auto gap-4">
        {/* Left Subsystem Telemetry */}
        <div className="flex items-center gap-4 shrink-0">
          <div className="flex items-center gap-1.5">
            <span
              className={`w-1.5 h-1.5 ${
                isApiOnline ? 'bg-radar-green shadow-[0_0_6px_rgba(16,185,129,0.7)]' : 'bg-radar-red'
              }`}
            />
            <span className="text-slate-300 font-semibold uppercase">API:</span>
            <span className={isApiOnline ? 'text-slate-200' : 'text-radar-red'}>
              {isApiOnline ? 'ONLINE' : 'UNREACHABLE'}
            </span>
          </div>

          <div className="flex items-center gap-1.5 border-l border-space-border pl-3">
            <span
              className={`w-1.5 h-1.5 ${
                isAiOnline ? 'bg-electric-cyan shadow-[0_0_6px_rgba(6,182,212,0.7)]' : 'bg-radar-amber'
              }`}
            />
            <span className="text-slate-300 font-semibold uppercase">AI ENGINE:</span>
            <span className="text-slate-200">
              {aiStatus?.llm?.default_provider ? aiStatus.llm.default_provider.toUpperCase() : 'STANDBY'}
            </span>
          </div>

          <div className="hidden sm:flex items-center gap-1.5 border-l border-space-border pl-3">
            <Database className="w-3 h-3 text-slate-500" />
            <span className="text-slate-300 font-semibold uppercase">DB:</span>
            <span className="text-slate-200">
              {health?.database ? health.database.toUpperCase() : 'CONNECTED'}
            </span>
          </div>

          <div className="hidden md:flex items-center gap-1.5 border-l border-space-border pl-3">
            <Cpu className="w-3 h-3 text-slate-500" />
            <span className="text-slate-300 font-semibold uppercase">DEVICE:</span>
            <span className="text-slate-200">
              {aiStatus?.device ? aiStatus.device.toUpperCase() : 'CPU'}
            </span>
          </div>
        </div>

        {/* Right Geographic Telemetry */}
        <div className="flex items-center gap-4 shrink-0 font-mono text-[10px]">
          {cursorCoordinates && (
            <div className="flex items-center gap-2">
              <Compass className="w-3 h-3 text-electric-cyan" />
              <span className="text-slate-400">CURSOR:</span>
              <span className="text-slate-200 font-bold">
                {cursorCoordinates[1].toFixed(4)}°N / {cursorCoordinates[0].toFixed(4)}°E
              </span>
            </div>
          )}

          <div className="border-l border-space-border pl-3 hidden lg:block">
            <span className="text-slate-400">ZOOM:</span>{' '}
            <span className="text-slate-200 font-bold">{viewport.zoom.toFixed(1)}x</span>
          </div>

          <div className="border-l border-space-border pl-3 text-electric-violet font-semibold hidden sm:block">
            ORBITMIND v1.0.0
          </div>
        </div>
      </div>
    </footer>
  );
};
