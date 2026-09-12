import React from 'react';
import { clsx } from 'clsx';

interface BrutalistPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  badge?: React.ReactNode;
  borderVariant?: 'default' | 'violet' | 'cyan' | 'alert';
  headerRight?: React.ReactNode;
  children: React.ReactNode;
}

export const BrutalistPanel: React.FC<BrutalistPanelProps> = ({
  title,
  subtitle,
  badge,
  borderVariant = 'default',
  headerRight,
  children,
  className,
  ...props
}) => {
  const borderStyles = {
    default: 'border-space-border hover:border-space-border-light',
    violet: 'border-electric-violet/60',
    cyan: 'border-electric-cyan/60',
    alert: 'border-radar-amber/70',
  };

  return (
    <div
      className={clsx(
        'bg-space-card/90 backdrop-blur-sm border transition-colors flex flex-col',
        borderStyles[borderVariant],
        className
      )}
      {...props}
    >
      {(title || badge || headerRight) && (
        <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-space-border bg-space-panel/80 select-none">
          <div className="flex items-center gap-2">
            {title && (
              <span className="font-mono text-xs uppercase tracking-wider font-bold text-slate-200">
                {title}
              </span>
            )}
            {subtitle && (
              <span className="font-mono text-[10px] text-slate-400 hidden sm:inline">
                // {subtitle}
              </span>
            )}
            {badge}
          </div>
          {headerRight && <div className="flex items-center gap-1.5">{headerRight}</div>}
        </div>
      )}
      <div className="flex-1 p-3.5">{children}</div>
    </div>
  );
};
