import React from 'react';
import { clsx } from 'clsx';

interface BrutalistBadgeProps {
  children: React.ReactNode;
  variant?: 'violet' | 'cyan' | 'green' | 'amber' | 'red' | 'neutral';
  size?: 'sm' | 'md';
  dot?: boolean;
  className?: string;
}

export const BrutalistBadge: React.FC<BrutalistBadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'sm',
  dot = false,
  className,
}) => {
  const variantStyles = {
    neutral: 'bg-space-panel text-slate-300 border-space-border',
    violet: 'bg-electric-violet/15 text-electric-violet border-electric-violet/40',
    cyan: 'bg-electric-cyan/15 text-electric-cyan border-electric-cyan/40',
    green: 'bg-radar-green/15 text-radar-green border-radar-green/40',
    amber: 'bg-radar-amber/15 text-radar-amber border-radar-amber/40',
    red: 'bg-radar-red/15 text-radar-red border-radar-red/40',
  };

  const dotColors = {
    neutral: 'bg-slate-400',
    violet: 'bg-electric-violet',
    cyan: 'bg-electric-cyan',
    green: 'bg-radar-green',
    amber: 'bg-radar-amber',
    red: 'bg-radar-red',
  };

  const sizeStyles = {
    sm: 'text-[10px] px-1.5 py-0.5 tracking-wider',
    md: 'text-xs px-2.5 py-1 tracking-widest',
  };

  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 font-mono uppercase font-semibold border select-none',
        sizeStyles[size],
        variantStyles[variant],
        className
      )}
    >
      {dot && (
        <span
          className={clsx(
            'w-1.5 h-1.5 rounded-none shrink-0 animate-pulse',
            dotColors[variant]
          )}
        />
      )}
      <span>{children}</span>
    </span>
  );
};
