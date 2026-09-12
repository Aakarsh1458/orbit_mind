import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { Globe, Cpu, Radio, Database, Terminal } from 'lucide-react';
import { useOrbitStore } from '../../store/useOrbitStore';
import { BrutalistBadge } from '../brutalist/BrutalistBadge';

export const TopNav: React.FC = () => {
  const location = useLocation();
  const { aiStatus, health } = useOrbitStore();
  const [utcTime, setUtcTime] = useState('');

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setUtcTime(
        now.toISOString().substring(11, 19) + ' UTC'
      );
    };
    updateTime();
    const timer = setInterval(updateTime, 1000);
    return () => clearInterval(timer);
  }, []);

  const navLinks = [
    { label: 'WORKSPACE', path: '/' },
    { label: 'OBSERVATORY', path: '/observatory' },
    { label: 'SATELLITES', path: '/satellites' },
    { label: 'AI MODELS', path: '/models' },
    { label: 'HISTORY', path: '/history' },
  ];

  const isMockMode = aiStatus?.ai_mode === 'mock';

  return (
    <header className="sticky top-0 z-40 bg-space-dark/95 backdrop-blur-md border-b border-space-border">
      <div className="flex items-center justify-between px-4 py-2.5">
        {/* Brand & Mission Identifier */}
        <div className="flex items-center gap-3.5">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-7 h-7 bg-electric-violet flex items-center justify-center font-mono font-bold text-white shadow-brutal text-sm group-hover:bg-electric-purple transition-colors">
              OM
            </div>
            <div className="flex flex-col">
              <span className="font-mono font-bold tracking-widest text-sm text-slate-100 flex items-center gap-1.5">
                ORBITMIND
                <span className="inline-block w-1.5 h-1.5 bg-electric-cyan animate-pulse" />
              </span>
              <span className="font-mono text-[9px] text-slate-400 tracking-wider hidden sm:inline">
                AI EARTH-OBSERVATION COMMAND
              </span>
            </div>
          </Link>

          {/* Mode Pill: DEMO/MOCK vs LIVE */}
          <div className="hidden md:flex items-center gap-2 pl-3 border-l border-space-border">
            <BrutalistBadge
              variant={isMockMode ? 'amber' : 'green'}
              dot
            >
              {isMockMode ? 'DEMO / MOCK' : 'LIVE PRODUCTION'}
            </BrutalistBadge>

            {aiStatus?.device && (
              <span className="font-mono text-[10px] text-slate-400 uppercase hidden lg:inline">
                COMPUTE: {aiStatus.device}
              </span>
            )}
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center gap-1">
          {navLinks.map((item) => {
            const isActive =
              location.pathname === item.path ||
              (item.path === '/' && location.pathname === '/workspace');
            return (
              <Link
                key={item.path}
                to={item.path}
                className={clsx(
                  'px-3 py-1.5 font-mono text-xs uppercase tracking-wider font-semibold border transition-all select-none',
                  isActive
                    ? 'bg-space-panel text-electric-cyan border-electric-cyan/60 shadow-brutal-cyan'
                    : 'bg-transparent text-slate-300 border-transparent hover:border-space-border hover:bg-space-panel/40'
                )}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Telemetry Clock & Quick Status */}
        <div className="hidden lg:flex items-center gap-3 pl-4 border-l border-space-border font-mono text-xs">
          <div className="flex items-center gap-1.5 text-slate-300">
            <span className="text-electric-cyan">{utcTime}</span>
          </div>
          <Link
            to="/"
            className="px-2.5 py-1 bg-electric-violet/20 border border-electric-violet text-electric-violet hover:bg-electric-violet hover:text-white transition-colors text-[11px] font-mono uppercase font-bold tracking-wider"
          >
            [ EXECUTE ]
          </Link>
        </div>
      </div>
    </header>
  );
};
