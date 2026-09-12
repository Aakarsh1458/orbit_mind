import React from 'react';
import { clsx } from 'clsx';

interface BrutalistButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'cyan';
  size?: 'sm' | 'md' | 'lg';
  icon?: React.ReactNode;
}

export const BrutalistButton: React.FC<BrutalistButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  icon,
  className,
  disabled,
  ...props
}) => {
  const baseStyles =
    'inline-flex items-center justify-center font-mono uppercase tracking-wider font-semibold border transition-all active:translate-x-0.5 active:translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none';

  const sizeStyles = {
    sm: 'px-2.5 py-1 text-xs gap-1.5',
    md: 'px-3.5 py-2 text-xs gap-2',
    lg: 'px-5 py-3 text-sm gap-2.5',
  };

  const variantStyles = {
    primary:
      'bg-electric-violet text-white border-electric-violet hover:bg-electric-purple shadow-brutal hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5',
    secondary:
      'bg-space-panel text-slate-200 border-space-border hover:border-slate-400 shadow-brutal hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5',
    cyan:
      'bg-electric-cyan text-space-black border-electric-cyan hover:bg-cyan-300 shadow-brutal-cyan hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5 font-bold',
    danger:
      'bg-radar-red text-white border-radar-red hover:bg-red-600 shadow-brutal hover:shadow-none hover:translate-x-0.5 hover:translate-y-0.5',
    ghost:
      'bg-transparent text-slate-300 border-transparent hover:border-space-border hover:bg-space-panel/60',
  };

  return (
    <button
      className={clsx(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      disabled={disabled}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </button>
  );
};
