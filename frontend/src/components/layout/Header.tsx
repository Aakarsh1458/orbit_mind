import React from 'react';
import { useChatStore } from '../../store/useChatStore';

export const Header: React.FC = () => {
  const { isAiAvailable, historySessions, isHistoryOpen, setIsHistoryOpen, startNewChat } = useChatStore();

  return (
    <header className="sticky top-0 z-30 w-full bg-white/85 backdrop-blur-md border-b border-charcoal-100/80 transition-all">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand & Identity */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-9 h-9 rounded-xl bg-gradient-to-br from-crimson-500 to-crimson-700 text-white shadow-sm shadow-crimson-500/20">
            {/* Orbital rings svg */}
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="3" />
              <path d="M4.93 19.07A10 10 0 0 1 19.07 4.93" />
              <path d="M19.07 19.07A10 10 0 0 1 4.93 4.93" />
            </svg>
            <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
              <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${isAiAvailable ? 'bg-emerald-400' : 'bg-amber-400'} opacity-75`}></span>
              <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${isAiAvailable ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
            </span>
          </div>

          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-lg tracking-tight text-charcoal-900">OrbitMind</span>
              <span className="hidden sm:inline-block text-[11px] font-medium tracking-wide uppercase px-2 py-0.5 rounded-full bg-crimson-50 text-crimson-700 border border-crimson-200/60">
                Satellite AI
              </span>
            </div>
            <p className="hidden md:block text-xs text-charcoal-400 -mt-0.5">
              Natural Language Earth Observation & Spectral Intelligence
            </p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          <button
            onClick={startNewChat}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-xl text-xs font-medium text-charcoal-700 hover:text-charcoal-900 bg-white/70 hover:bg-white border border-charcoal-200/80 shadow-sm transition-all hover:shadow hover:border-charcoal-300 active:scale-95"
            title="Start a fresh conversation"
          >
            <svg className="w-3.5 h-3.5 text-crimson-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M12 4v16m8-8H4" />
            </svg>
            <span>New Chat</span>
          </button>

          <button
            onClick={() => setIsHistoryOpen(!isHistoryOpen)}
            className={`relative flex items-center justify-center w-9 h-9 rounded-xl border transition-all active:scale-95 ${
              isHistoryOpen
                ? 'bg-crimson-50 text-crimson-700 border-crimson-300 shadow-sm'
                : 'bg-white/70 text-charcoal-600 hover:text-charcoal-900 hover:bg-white border-charcoal-200/80 shadow-sm'
            }`}
            title="Conversation History"
            aria-label="Toggle Conversation History"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {historySessions.length > 0 && (
              <span className="absolute -top-1 -right-1 flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-bold bg-charcoal-900 text-white shadow-sm">
                {historySessions.length}
              </span>
            )}
          </button>
        </div>
      </div>
    </header>
  );
};
