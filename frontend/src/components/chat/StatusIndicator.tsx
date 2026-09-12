import React from 'react';

interface StatusIndicatorProps {
  status: string | null;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ status }) => {
  const displayStatus = status || 'Analyzing satellite observations...';

  return (
    <div className="flex items-center gap-3 py-3 px-4 rounded-2xl bg-white/70 backdrop-blur-md border border-charcoal-100 shadow-sm max-w-fit animate-fade-in my-3">
      {/* Pulsing indicator with crimson glow */}
      <div className="relative flex items-center justify-center w-5 h-5">
        <span className="animate-ping absolute inline-flex h-3 w-3 rounded-full bg-crimson-400 opacity-60" />
        <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-crimson-600" />
      </div>

      <span className="text-xs font-medium text-charcoal-700 tracking-tight">
        {displayStatus}
      </span>
    </div>
  );
};
