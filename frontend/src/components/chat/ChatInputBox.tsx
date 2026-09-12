import React, { useState, useRef, useEffect } from 'react';
import { useChatStore } from '../../store/useChatStore';
import { AttachmentPreview } from './AttachmentPreview';

interface ChatInputBoxProps {
  onSendMessage: (prompt: string) => void;
  inputRef?: React.RefObject<HTMLTextAreaElement>;
}

export const ChatInputBox: React.FC<ChatInputBoxProps> = ({ onSendMessage }) => {
  const [prompt, setPrompt] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const internalRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    attachments,
    addAttachment,
    removeAttachment,
    isAnalyzing,
  } = useChatStore();

  // Auto-resize textarea height
  useEffect(() => {
    const textarea = internalRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    textarea.style.height = `${Math.min(textarea.scrollHeight, 160)}px`;
  }, [prompt]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (isAnalyzing) return;
    if (!prompt.trim() && attachments.length === 0) return;

    onSendMessage(prompt);
    setPrompt('');
    if (internalRef.current) {
      internalRef.current.style.height = 'auto';
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;
    for (let i = 0; i < files.length; i++) {
      addAttachment(files[i]);
    }
    e.target.value = '';
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (!files) return;
    for (let i = 0; i < files.length; i++) {
      if (files[i].type.startsWith('image/') || files[i].name.endsWith('.tif') || files[i].name.endsWith('.tiff')) {
        addAttachment(files[i]);
      }
    }
  };

  const canSubmit = !isAnalyzing && (prompt.trim().length > 0 || attachments.length > 0);

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4 sm:pb-6">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative rounded-3xl bg-white/90 backdrop-blur-xl border transition-all shadow-glass p-2 sm:p-2.5 ${
          isDragging
            ? 'border-crimson-500 ring-2 ring-crimson-500/20 bg-crimson-50/40'
            : 'border-charcoal-200/90 focus-within:border-crimson-500/80 focus-within:ring-2 focus-within:ring-crimson-500/10'
        }`}
      >
        {/* Pending image previews */}
        <AttachmentPreview attachments={attachments} onRemove={removeAttachment} />

        {/* Input area */}
        <div className="flex items-end gap-2">
          {/* File attachment trigger */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp,image/tiff,.tif,.tiff"
            multiple
            className="hidden"
            onChange={handleFileChange}
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="flex items-center justify-center w-10 h-10 rounded-2xl text-charcoal-400 hover:text-charcoal-700 hover:bg-charcoal-100/70 transition-colors shrink-0"
            title="Attach satellite image (PNG, JPG, WEBP, TIFF)"
            aria-label="Attach satellite image"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
          </button>

          {/* Textarea */}
          <textarea
            ref={internalRef}
            rows={1}
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              attachments.length > 0
                ? 'Ask about this satellite imagery...'
                : 'Ask Earth anything or drop satellite imagery...'
            }
            className="flex-1 max-h-40 min-h-[40px] py-2 px-1 bg-transparent resize-none text-charcoal-900 placeholder:text-charcoal-400 text-sm sm:text-base focus:outline-none leading-relaxed"
          />

          {/* Send Button */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!canSubmit}
            className={`flex items-center justify-center w-10 h-10 rounded-2xl transition-all shrink-0 ${
              canSubmit
                ? 'bg-crimson-600 hover:bg-crimson-700 text-white shadow-sm shadow-crimson-600/30 active:scale-95'
                : 'bg-charcoal-100 text-charcoal-300 cursor-not-allowed'
            }`}
            title="Send query (Enter)"
            aria-label="Send query"
          >
            {isAnalyzing ? (
              <svg className="animate-spin w-4 h-4 text-white" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            ) : (
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 10l7-7m0 0l7 7m-7-7v18" />
              </svg>
            )}
          </button>
        </div>
      </div>

      <div className="flex items-center justify-between px-3 mt-2 text-[11px] text-charcoal-400">
        <span>Press <kbd className="font-mono bg-charcoal-100/70 px-1 py-0.5 rounded text-[10px] text-charcoal-500">Enter</kbd> to send, <kbd className="font-mono bg-charcoal-100/70 px-1 py-0.5 rounded text-[10px] text-charcoal-500">Shift+Enter</kbd> for newline</span>
        <span className="hidden sm:inline">Supports Sentinel, Landsat, and SAR formats</span>
      </div>
    </div>
  );
};
