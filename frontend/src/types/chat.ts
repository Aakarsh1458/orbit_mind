export interface ImageAttachment {
  id: string;
  file?: File;
  previewUrl: string;
  filename: string;
  sizeBytes: number;
  serverImageryId?: string;
  isUploading?: boolean;
}

export interface SourceCitation {
  id: string;
  title: string;
  type: string;
  sensor?: string;
  date?: string;
  resolution?: string;
  path?: string;
  details?: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  attachments?: ImageAttachment[];
  sources?: SourceCitation[];
  followUpSuggestions?: string[];
  geojson?: any;
  rasterUrl?: string;
  isStreaming?: boolean;
  error?: string;
}

export interface ConversationSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount?: number;
}
