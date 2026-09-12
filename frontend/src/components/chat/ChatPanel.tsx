import React, { useEffect, useRef } from 'react';
import { useOrbitStore } from '../../store/useOrbitStore';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { ExecutionStateBox } from './ExecutionStateBox';
import { Terminal, Trash2 } from 'lucide-react';

export const ChatPanel: React.FC = () => {
  const { messages, isExecuting, conversationId, setMessages, resetExecution } = useOrbitStore();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isExecuting]);

  const handleClear = () => {
    setMessages([]);
    resetExecution();
  };

  return (
    <div className="flex flex-col h-full bg-space-card/90 border border-space-border">
      {/* Panel Top Header */}
      <div className="flex items-center justify-between px-3.5 py-2.5 border-b border-space-border bg-space-panel select-none">
        <div className="flex items-center gap-2">
          <Terminal className="w-4 h-4 text-electric-cyan" />
          <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-200">
            ORBITMIND AI CONSOLE
          </span>
          <span className="font-mono text-[10px] text-slate-400 hidden sm:inline">
            // SESSION: {conversationId ? conversationId.substring(0, 8) : 'NEW'}
          </span>
        </div>

        {messages.length > 0 && (
          <button
            onClick={handleClear}
            className="text-slate-500 hover:text-radar-red p-1 transition-colors"
            title="Clear conversation"
          >
            <Trash2 className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {/* Message Stream */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-2">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500 select-none">
            <div className="w-10 h-10 border border-dashed border-space-border flex items-center justify-center text-electric-violet mb-3">
              <Terminal className="w-5 h-5" />
            </div>
            <div className="font-mono text-xs uppercase font-bold text-slate-300">
              ORBITAL ANALYSIS READY
            </div>
            <p className="font-mono text-[11px] text-slate-400 max-w-[280px] mt-1">
              Ask a natural-language question about Earth observation, urban expansion, land cover, or radar backscatter.
            </p>
          </div>
        ) : (
          <>
            {messages.map((m) => (
              <ChatMessage key={m.id} message={m} />
            ))}
            <ExecutionStateBox />
          </>
        )}
      </div>

      {/* Chat Command Input Bar */}
      <ChatInput />
    </div>
  );
};
