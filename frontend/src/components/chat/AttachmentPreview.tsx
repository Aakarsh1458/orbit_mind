import React from 'react';
import { ImageAttachment } from '../../types/chat';

interface AttachmentPreviewProps {
  attachments: ImageAttachment[];
  onRemove: (id: string) => void;
}

export const AttachmentPreview: React.FC<AttachmentPreviewProps> = ({ attachments, onRemove }) => {
  if (attachments.length === 0) return null;

  const formatBytes = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="flex items-center gap-2.5 overflow-x-auto py-2 px-1 mb-2 scrollbar-none">
      {attachments.map((att) => (
        <div
          key={att.id}
          className="relative group flex items-center gap-2.5 pl-1.5 pr-3 py-1.5 rounded-xl bg-white/90 border border-charcoal-200/80 shadow-sm shrink-0 animate-fade-in"
        >
          {att.previewUrl ? (
            <img
              src={att.previewUrl}
              alt={att.filename}
              className="w-10 h-10 object-cover rounded-lg border border-charcoal-100"
            />
          ) : (
            <div className="w-10 h-10 rounded-lg bg-charcoal-100 flex items-center justify-center text-charcoal-400">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
          )}

          <div className="flex flex-col min-w-0 pr-1">
            <span className="text-xs font-medium text-charcoal-800 truncate max-w-[120px]">
              {att.filename}
            </span>
            <span className="text-[10px] text-charcoal-400">
              {formatBytes(att.sizeBytes)}
            </span>
          </div>

          <button
            type="button"
            onClick={() => onRemove(att.id)}
            className="w-5 h-5 rounded-full bg-charcoal-100 hover:bg-crimson-100 text-charcoal-400 hover:text-crimson-600 flex items-center justify-center transition-colors text-xs"
            aria-label="Remove image"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
};
