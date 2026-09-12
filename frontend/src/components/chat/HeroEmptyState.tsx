import React from 'react';
import { useChatStore } from '../../store/useChatStore';

const EXAMPLE_PROMPTS = [
  {
    icon: '🏙️',
    title: 'Urban Expansion',
    prompt: 'Where did urban expansion occur and what was the change in built-up density?',
  },
  {
    icon: '🌱',
    title: 'Vegetation & Agriculture',
    prompt: 'Assess crop health and compute NDVI vegetative stress across this region.',
  },
  {
    icon: '☁️',
    title: 'Cloud Removal',
    prompt: 'Remove dense cloud cover and reconstruct clear multispectral surface bands.',
  },
  {
    icon: '💧',
    title: 'Water Body Shift',
    prompt: 'Detect surface water shrinkage and measure shoreline displacement over time.',
  },
];

interface HeroEmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
}

export const HeroEmptyState: React.FC<HeroEmptyStateProps> = ({ onSelectPrompt }) => {
  return (
    <div className="flex flex-col items-center justify-center text-center px-4 py-8 md:py-16 max-w-2xl mx-auto animate-fade-in">
      {/* Visual Emblem */}
      <div className="relative mb-6">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-crimson-600 via-crimson-500 to-amber-500 flex items-center justify-center text-white shadow-lg shadow-crimson-500/20">
          <svg className="w-8 h-8" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
            <circle cx="12" cy="12" r="10" />
            <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
            <path d="M2 12h20" />
          </svg>
        </div>
        <div className="absolute -inset-1 rounded-2xl bg-crimson-500/15 blur-xl -z-10" />
      </div>

      {/* Main Heading */}
      <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-charcoal-900 mb-3">
        Ask Earth anything.
      </h1>
      <p className="text-sm sm:text-base text-charcoal-500 leading-relaxed max-w-lg mb-8">
        Ask questions in natural language, upload satellite imagery, and receive grounded remote-sensing insights with verifiable evidence.
      </p>

      {/* Suggestion Pills */}
      <div className="w-full grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-left">
        {EXAMPLE_PROMPTS.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(item.prompt)}
            className="group p-3.5 rounded-2xl bg-white/70 hover:bg-white border border-charcoal-100 hover:border-crimson-200/80 shadow-sm hover:shadow-md transition-all text-left flex items-start gap-3 active:scale-[0.99]"
          >
            <span className="text-lg select-none group-hover:scale-110 transition-transform">
              {item.icon}
            </span>
            <div className="flex-1 min-w-0">
              <span className="block text-xs font-semibold text-charcoal-900 group-hover:text-crimson-600 transition-colors">
                {item.title}
              </span>
              <p className="text-[11px] text-charcoal-500 line-clamp-2 mt-0.5 leading-snug">
                {item.prompt}
              </p>
            </div>
            <svg
              className="w-4 h-4 text-charcoal-300 group-hover:text-crimson-600 group-hover:translate-x-0.5 transition-all mt-0.5 shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        ))}
      </div>
    </div>
  );
};
