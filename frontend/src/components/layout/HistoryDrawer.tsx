import React, { useEffect } from 'react';
import { useChatStore } from '../../store/useChatStore';

export const HistoryDrawer: React.FC = () => {
  const {
    historySessions,
    isHistoryOpen,
    setIsHistoryOpen,
    conversationId,
    loadSession,
    startNewChat,
    fetchHistory,
  } = useChatStore();

  useEffect(() => {
    if (isHistoryOpen) {
      fetchHistory();
    }
  }, [isHistoryOpen, fetchHistory]);

  if (!isHistoryOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-charcoal-950/20 backdrop-blur-sm transition-opacity animate-fade-in"
        onClick={() => setIsHistoryOpen(false)}
      />

      <div className="fixed inset-y-0 right-0 max-w-full flex pl-10">
        <div className="w-screen max-w-sm bg-white/95 backdrop-blur-xl border-l border-charcoal-100 shadow-2xl flex flex-col transform transition-all duration-300 ease-out animate-slide-in">
          {/* Header */}
          <div className="p-5 border-b border-charcoal-100 flex items-center justify-between">
            <div>
              <h2 className="text-base font-semibold text-charcoal-900">Conversations</h2>
              <p className="text-xs text-charcoal-500">Past satellite intelligence sessions</p>
            </div>
            <button
              onClick={() => setIsHistoryOpen(false)}
              className="p-1.5 rounded-lg text-charcoal-400 hover:text-charcoal-700 hover:bg-charcoal-100/60 transition"
              aria-label="Close drawer"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* New Chat Button */}
          <div className="p-4 border-b border-charcoal-100/70">
            <button
              onClick={() => {
                startNewChat();
                setIsHistoryOpen(false);
              }}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-crimson-600 hover:bg-crimson-700 text-white font-medium text-sm shadow-sm transition active:scale-[0.98]"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
              </svg>
              <span>Start New Inquiry</span>
            </button>
          </div>

          {/* Sessions List */}
          <div className="flex-1 overflow-y-auto p-3 space-y-1.5">
            {historySessions.length === 0 ? (
              <div className="py-12 text-center text-charcoal-400">
                <svg className="w-8 h-8 mx-auto mb-2 text-charcoal-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
                <p className="text-xs">No prior conversations found.</p>
              </div>
            ) : (
              historySessions.map((session) => {
                const isActive = session.id === conversationId;
                return (
                  <button
                    key={session.id}
                    onClick={() => loadSession(session.id)}
                    className={`w-full text-left p-3 rounded-xl transition-all border ${
                      isActive
                        ? 'bg-crimson-50/70 border-crimson-200 text-charcoal-900 shadow-sm'
                        : 'bg-white/60 hover:bg-charcoal-50/80 border-transparent hover:border-charcoal-200/50 text-charcoal-700'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium text-xs leading-snug line-clamp-1 text-charcoal-900">
                        {session.title || 'Satellite Observation'}
                      </p>
                      {isActive && (
                        <span className="w-1.5 h-1.5 rounded-full bg-crimson-600 shrink-0 mt-1" />
                      )}
                    </div>
                    <div className="mt-1 flex items-center justify-between text-[10px] text-charcoal-400">
                      <span>{new Date(session.updatedAt || session.createdAt).toLocaleDateString()}</span>
                      <span>{session.messageCount} messages</span>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
