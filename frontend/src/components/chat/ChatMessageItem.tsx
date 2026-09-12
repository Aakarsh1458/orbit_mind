import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { ChatMessage } from '../../types/chat';
import { EvidenceAccordion } from './EvidenceAccordion';
import { useChatStore } from '../../store/useChatStore';

interface ChatMessageItemProps {
  message: ChatMessage;
  onSelectSuggestion?: (prompt: string) => void;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  onSelectSuggestion,
}) => {
  const isUser = message.role === 'user';
  const { openMapModal } = useChatStore();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOpenMap = () => {
    openMapModal({
      geojson: message.geojson,
      title: 'Satellite Analysis Coverage',
    });
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-6 animate-fade-in">
        <div className="max-w-xl">
          {/* User Attachments */}
          {message.attachments && message.attachments.length > 0 && (
            <div className="flex flex-wrap gap-2 justify-end mb-2">
              {message.attachments.map((att) => (
                <div
                  key={att.id}
                  className="overflow-hidden rounded-xl border border-charcoal-200/80 shadow-sm bg-white"
                >
                  {att.previewUrl ? (
                    <img
                      src={att.previewUrl}
                      alt={att.filename}
                      className="w-24 h-24 object-cover"
                    />
                  ) : (
                    <div className="w-24 h-24 flex items-center justify-center bg-charcoal-100 text-xs text-charcoal-500">
                      {att.filename}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* User Text Bubble */}
          <div className="bg-charcoal-900 text-white px-4 py-3 rounded-2xl rounded-tr-sm shadow-sm text-sm leading-relaxed">
            {message.content}
          </div>
          <div className="text-right mt-1 text-[10px] text-charcoal-400 font-mono">
            {message.timestamp}
          </div>
        </div>
      </div>
    );
  }

  // Assistant Message (Editorial AI layout)
  return (
    <div className="flex items-start gap-3.5 mb-8 animate-fade-in group">
      {/* Orbital Avatar */}
      <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-crimson-600 to-crimson-800 text-white flex items-center justify-center shrink-0 shadow-sm shadow-crimson-600/20 mt-1">
        <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="3" />
          <path d="M4.93 19.07A10 10 0 0 1 19.07 4.93" />
        </svg>
      </div>

      {/* Content Container */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-xs text-charcoal-900">OrbitMind</span>
            <span className="text-[10px] text-charcoal-400 font-mono">{message.timestamp}</span>
          </div>

          <button
            onClick={handleCopy}
            className="opacity-0 group-hover:opacity-100 transition-opacity text-[11px] text-charcoal-400 hover:text-charcoal-700 flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-charcoal-100"
            title="Copy answer"
          >
            {copied ? (
              <span className="text-emerald-600 font-medium">Copied!</span>
            ) : (
              <>
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                <span>Copy</span>
              </>
            )}
          </button>
        </div>

        {/* Markdown Content */}
        <div className="text-charcoal-800 text-sm leading-relaxed prose prose-sm max-w-none prose-headings:text-charcoal-900 prose-headings:font-semibold prose-a:text-crimson-600 prose-strong:text-charcoal-900 prose-code:text-charcoal-800 prose-code:bg-charcoal-100/70 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Map Handoff Action (if spatial GeoJSON exists) */}
        {message.geojson && (
          <div className="mt-3.5">
            <button
              onClick={handleOpenMap}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-medium bg-crimson-50 hover:bg-crimson-100/80 text-crimson-700 border border-crimson-200 transition active:scale-[0.98]"
            >
              <svg className="w-4 h-4 text-crimson-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              <span>View analysis on map</span>
              <span className="text-crimson-400">→</span>
            </button>
          </div>
        )}

        {/* RAG Evidence & Sources */}
        {message.sources && message.sources.length > 0 && (
          <EvidenceAccordion sources={message.sources} />
        )}

        {/* Follow-up Suggestions */}
        {message.followUpSuggestions && message.followUpSuggestions.length > 0 && onSelectSuggestion && (
          <div className="mt-4 pt-3 flex flex-wrap gap-1.5">
            {message.followUpSuggestions.map((sug, idx) => (
              <button
                key={idx}
                onClick={() => onSelectSuggestion(sug)}
                className="text-xs px-3 py-1.5 rounded-full bg-white hover:bg-charcoal-50 text-charcoal-600 hover:text-crimson-700 border border-charcoal-200/80 hover:border-crimson-300 transition-all active:scale-[0.98] shadow-2xs"
              >
                {sug}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
