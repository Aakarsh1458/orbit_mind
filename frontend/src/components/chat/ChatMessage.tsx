import React from 'react';
import { ChatMessage as ChatMessageType, useOrbitStore } from '../../store/useOrbitStore';
import { BrutalistBadge } from '../brutalist/BrutalistBadge';
import { User, Bot, Sparkles, ChevronRight } from 'lucide-react';
import { useMapStore } from '../../store/useMapStore';

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const { setActiveGeoJSON } = useMapStore();
  const { executePrompt, isExecuting } = useOrbitStore();

  const handleInspectMap = () => {
    if (message.responsePayload?.geojson) {
      setActiveGeoJSON(message.responsePayload.geojson);
    }
  };

  return (
    <div
      className={`border p-3 my-2.5 transition-colors ${
        isUser
          ? 'bg-space-panel/80 border-space-border ml-4 text-slate-200'
          : 'bg-space-card/95 border-electric-violet/40 mr-4 shadow-brutal text-slate-100'
      }`}
    >
      {/* Header bar */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b border-space-border font-mono text-[11px]">
        <div className="flex items-center gap-2">
          {isUser ? (
            <div className="w-5 h-5 bg-slate-700 flex items-center justify-center text-slate-200">
              <User className="w-3 h-3" />
            </div>
          ) : (
            <div className="w-5 h-5 bg-electric-violet flex items-center justify-center text-white">
              <Bot className="w-3 h-3" />
            </div>
          )}
          <span className="font-bold uppercase tracking-wider text-slate-300">
            {isUser ? 'OPERATOR' : 'ORBITMIND AI'}
          </span>
          {message.task && (
            <BrutalistBadge variant="violet" size="sm">
              {message.task}
            </BrutalistBadge>
          )}
        </div>

        <span className="text-[10px] text-slate-400">{message.timestamp}</span>
      </div>

      {/* Message Content */}
      <div className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
        {message.content}
      </div>

      {/* Structured Result Highlights if present */}
      {message.responsePayload && (
        <div className="mt-3 pt-2.5 border-t border-space-border font-mono text-xs space-y-2">
          <div className="grid grid-cols-2 gap-2 text-[11px]">
            {message.responsePayload.analysis?.model && (
              <div className="bg-space-panel p-2 border border-space-border">
                <span className="text-slate-400 block text-[9px] uppercase">MODEL:</span>
                <span className="text-electric-cyan font-bold">
                  {message.responsePayload.analysis.model}
                </span>
              </div>
            )}

            {message.responsePayload.statistics?.area_km2 !== undefined && (
              <div className="bg-space-panel p-2 border border-space-border">
                <span className="text-slate-400 block text-[9px] uppercase">DETECTED AREA:</span>
                <span className="text-radar-green font-bold">
                  {message.responsePayload.statistics.area_km2.toFixed(2)} km²
                </span>
              </div>
            )}
          </div>

          {message.responsePayload.geojson && (
            <button
              onClick={handleInspectMap}
              className="w-full mt-1 py-1 px-2 bg-space-dark border border-electric-cyan/60 text-electric-cyan hover:bg-electric-cyan hover:text-space-black transition-all text-center text-[10px] uppercase font-bold tracking-widest"
            >
              [ SYNC RESULT TO MAP VIEWPORT ]
            </button>
          )}

          {/* Dynamic Proactive Follow-up Suggestion Chips */}
          {!isUser && message.responsePayload?.follow_up_suggestions && message.responsePayload.follow_up_suggestions.length > 0 && (
            <div className="mt-3 pt-2.5 border-t border-space-border/70 font-mono">
              <div className="flex items-center gap-1.5 text-[10px] text-slate-400 uppercase tracking-wider mb-2">
                <Sparkles className="w-3 h-3 text-electric-cyan" />
                <span>Suggested Inquiries / Follow-Ups:</span>
              </div>
              <div className="flex flex-wrap gap-1.5">
                {message.responsePayload.follow_up_suggestions.map((suggestion, idx) => (
                  <button
                    key={idx}
                    type="button"
                    disabled={isExecuting}
                    onClick={() => executePrompt(suggestion)}
                    className="text-[11px] px-2.5 py-1 bg-space-panel/90 hover:bg-electric-cyan/20 border border-electric-cyan/40 hover:border-electric-cyan text-slate-200 hover:text-white transition-all text-left flex items-center gap-1.5 disabled:opacity-40 disabled:cursor-not-allowed group shadow-sm"
                  >
                    <span className="text-electric-cyan group-hover:text-white font-bold">&gt;</span>
                    <span>{suggestion}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
