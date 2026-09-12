import React, { useRef, useEffect } from 'react';
import { useChatStore } from '../../store/useChatStore';
import { HeroEmptyState } from './HeroEmptyState';
import { ChatMessageItem } from './ChatMessageItem';
import { StatusIndicator } from './StatusIndicator';
import { ChatInputBox } from './ChatInputBox';

export const ChatContainer: React.FC = () => {
  const {
    messages,
    isAnalyzing,
    friendlyStatus,
    errorMessage,
    sendMessage,
  } = useChatStore();

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isAnalyzing, friendlyStatus]);

  const handleSelectPrompt = (promptText: string) => {
    sendMessage(promptText);
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="relative flex-1 flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto w-full">
      {/* Scrollable messages or Empty hero */}
      <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6 scrollbar-thin">
        {isEmpty ? (
          <div className="min-h-full flex items-center justify-center">
            <HeroEmptyState onSelectPrompt={handleSelectPrompt} />
          </div>
        ) : (
          <div className="max-w-3xl mx-auto">
            {messages.map((msg) => (
              <ChatMessageItem
                key={msg.id}
                message={msg}
                onSelectSuggestion={handleSelectPrompt}
              />
            ))}

            {isAnalyzing && (
              <StatusIndicator status={friendlyStatus} />
            )}

            {errorMessage && !isAnalyzing && (
              <div className="my-4 p-3.5 rounded-xl bg-crimson-50 border border-crimson-200 text-crimson-800 text-xs flex items-center gap-2.5">
                <svg className="w-4 h-4 text-crimson-600 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span>{errorMessage}</span>
              </div>
            )}

            <div ref={messagesEndRef} className="h-4" />
          </div>
        )}
      </div>

      {/* Sticky Bottom Glass Input */}
      <div className="shrink-0">
        <ChatInputBox onSendMessage={sendMessage} />
      </div>
    </div>
  );
};
