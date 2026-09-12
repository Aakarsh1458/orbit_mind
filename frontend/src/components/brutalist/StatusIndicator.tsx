import React from 'react';
import { clsx } from 'clsx';

interface StatusIndicatorProps {
  label: string;
  status?: 'online' | 'ready' | 'processing' | 'offline' | 'error';
  sublabel?: string;
  className?: string;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  label,
  status = 'online',
  sublabel,
  className,
}) => {
  const statusColors = {
    online: 'bg-radar-green border-radar-green/60 shadow-[0_0_8px_rgba(16,185,129,0.6)]',
    ready: 'bg-electric-cyan border-electric-cyan/60 shadow-[0_0_8px_rgba(6,182,212,0.6)]',
    processing: 'bg-electric-violet border-electric-violet/60 animate-pulse',
    offline: 'bg-slate-600 border-slate-500',
    error: 'bg-radar-red border-radar-red/60 shadow-[0_0_8px_rgba(239,68,68,0.6)]',
  };

  return (
    <div className={clsx('flex items-center gap-2 font-mono text-xs select-none', className)}>
      <span className={clsx('w-2 h-2 border shrink-0', statusColors[status])} />
      <span className="font-semibold tracking-wider text-slate-200 uppercase">{label}</span>
      {sublabel && <span className="text-[10px] text-slate-500">// {sublabel}</span>}
    </div>
  );
};
