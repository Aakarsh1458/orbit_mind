import { create } from 'zustand';
import { ChatMessage, ImageAttachment, SourceCitation, ConversationSession } from '../types/chat';
import { streamChat, sendChat } from '../api/chatApi';
import { uploadImagery } from '../api/imageryApi';
import { listConversations, getMessages } from '../api/conversationsApi';
import { checkAiAvailability } from '../api/statusApi';

interface ChatStoreState {
  conversationId: string | null;
  messages: ChatMessage[];
  attachments: ImageAttachment[];
  isAnalyzing: boolean;
  friendlyStatus: string | null;
  errorMessage: string | null;
  isAiAvailable: boolean;
  
  // History & Session Navigation
  historySessions: ConversationSession[];
  isHistoryOpen: boolean;
  
  // Map Result Handoff
  mapModalData: {
    isOpen: boolean;
    geojson?: any;
    title?: string;
    rasterPath?: string;
  };

  // Actions
  initialize: () => Promise<void>;
  setConversationId: (id: string | null) => void;
  addAttachment: (file: File) => void;
  removeAttachment: (id: string) => void;
  clearAttachments: () => void;
  setIsHistoryOpen: (isOpen: boolean) => void;
  openMapModal: (data: { geojson?: any; title?: string; rasterPath?: string }) => void;
  closeMapModal: () => void;
  startNewChat: () => void;
  loadSession: (sessionId: string) => Promise<void>;
  fetchHistory: () => Promise<void>;
  sendMessage: (prompt: string) => Promise<void>;
}

export const useChatStore = create<ChatStoreState>((set, get) => ({
  conversationId: null,
  messages: [],
  attachments: [],
  isAnalyzing: false,
  friendlyStatus: null,
  errorMessage: null,
  isAiAvailable: true,
  historySessions: [],
  isHistoryOpen: false,
  mapModalData: { isOpen: false },

  initialize: async () => {
    try {
      const [status, _] = await Promise.allSettled([
        checkAiAvailability(),
        get().fetchHistory(),
      ]);
      if (status.status === 'fulfilled') {
        set({ isAiAvailable: status.value.available });
      }
    } catch (e) {
      console.warn('Initial store setup error:', e);
    }
  },

  setConversationId: (id) => set({ conversationId: id }),

  addAttachment: (file: File) => {
    const previewUrl = URL.createObjectURL(file);
    const newAttachment: ImageAttachment = {
      id: `att_${Date.now()}_${Math.random().toString(36).substring(2, 7)}`,
      file,
      previewUrl,
      filename: file.name,
      sizeBytes: file.size,
      isUploading: false,
    };
    set((state) => ({
      attachments: [...state.attachments, newAttachment],
    }));
  },

  removeAttachment: (id: string) => {
    set((state) => {
      const att = state.attachments.find((a) => a.id === id);
      if (att?.previewUrl) {
        URL.revokeObjectURL(att.previewUrl);
      }
      return {
        attachments: state.attachments.filter((a) => a.id !== id),
      };
    });
  },

  clearAttachments: () => {
    get().attachments.forEach((a) => {
      if (a.previewUrl) URL.revokeObjectURL(a.previewUrl);
    });
    set({ attachments: [] });
  },

  setIsHistoryOpen: (isOpen: boolean) => set({ isHistoryOpen: isOpen }),

  openMapModal: (data) =>
    set({
      mapModalData: {
        isOpen: true,
        geojson: data.geojson,
        title: data.title || 'Satellite Analysis Result',
        rasterPath: data.rasterPath,
      },
    }),

  closeMapModal: () => set({ mapModalData: { isOpen: false } }),

  startNewChat: () => {
    get().clearAttachments();
    set({
      conversationId: null,
      messages: [],
      friendlyStatus: null,
      errorMessage: null,
      isAnalyzing: false,
      isHistoryOpen: false,
    });
  },

  fetchHistory: async () => {
    try {
      const res = await listConversations(30, 0);
      const sessions: ConversationSession[] = (res || []).map((c: any) => ({
        id: c.id,
        title: c.title || 'Earth Observation Session',
        createdAt: c.created_at,
        updatedAt: c.updated_at,
        messageCount: c.message_count || 0,
      }));
      set({ historySessions: sessions });
    } catch (err) {
      console.warn('Could not fetch conversation history:', err);
    }
  },

  loadSession: async (sessionId: string) => {
    try {
      set({ isAnalyzing: true, friendlyStatus: 'Loading conversation...' });
      const res = await getMessages(sessionId, 50);
      const formatted: ChatMessage[] = (res.messages || []).map((m: any) => ({
        id: m.id || `msg_${Date.now()}`,
        role: m.role === 'assistant' ? 'assistant' : 'user',
        content: m.content || '',
        timestamp: new Date(m.created_at || Date.now()).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
        }),
      }));

      set({
        conversationId: sessionId,
        messages: formatted,
        isHistoryOpen: false,
        isAnalyzing: false,
        friendlyStatus: null,
      });
    } catch (err: any) {
      set({
        isAnalyzing: false,
        friendlyStatus: null,
        errorMessage: `Failed to load conversation: ${err.message || ''}`,
      });
    }
  },

  sendMessage: async (prompt: string) => {
    const { conversationId, attachments, clearAttachments } = get();
    const cleanPrompt = prompt.trim();
    if (!cleanPrompt && attachments.length === 0) return;

    set({ isAnalyzing: true, errorMessage: null, friendlyStatus: 'Preparing your inquiry...' });

    // Step 1: Upload any attached files to backend to get real server imagery IDs
    const uploadedIds: string[] = [];
    const activeAttachments = [...attachments];

    for (let i = 0; i < activeAttachments.length; i++) {
      const att = activeAttachments[i];
      if (att.serverImageryId) {
        uploadedIds.push(att.serverImageryId);
      } else if (att.file) {
        try {
          set({ friendlyStatus: `Uploading ${att.filename}...` });
          const res = await uploadImagery(att.file);
          if (res?.id) {
            uploadedIds.push(res.id);
            att.serverImageryId = res.id;
          }
        } catch (uploadErr: any) {
          console.warn('Failed to upload image:', uploadErr);
        }
      }
    }

    // Step 2: Append user message to conversation
    const userMsgId = `user_${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: cleanPrompt,
      attachments: activeAttachments,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    set((state) => ({
      messages: [...state.messages, userMsg],
      friendlyStatus: 'Analyzing satellite imagery...',
    }));
    clearAttachments();

    // Human-friendly mapping of backend execution stages
    const STAGE_LABELS: Record<string, string> = {
      planning: 'Understanding your question...',
      model_selection: 'Selecting satellite intelligence models...',
      preprocessing: 'Preparing satellite imagery bands...',
      inference: 'Analyzing satellite imagery...',
      validation: 'Verifying geospatial accuracy...',
      evidence_generation: 'Compiling evidence and spatial metrics...',
      response_generation: 'Synthesizing natural response...',
    };

    const payload = {
      message: cleanPrompt,
      conversation_id: conversationId,
      imagery_ids: uploadedIds,
    };

    // Step 3: Stream from FastAPI backend with progressive human states
    try {
      await streamChat(payload, {
        onStatus: (stage) => {
          const friendly = STAGE_LABELS[stage] || 'Processing Earth observations...';
          set({ friendlyStatus: friendly });
        },
        onCompleted: (result) => {
          // Format sources / evidence from backend
          const sources: SourceCitation[] = [];
          if (result.evidence && Array.isArray(result.evidence)) {
            result.evidence.forEach((ev: any, idx: number) => {
              sources.push({
                id: `src_${idx}_${Date.now()}`,
                title: ev.type?.replace(/_/g, ' ').toUpperCase() || 'Observation Artifact',
                type: ev.type || 'satellite_layer',
                path: ev.path || ev.paths?.[0],
                sensor: ev.sensor || 'Sentinel',
                resolution: ev.resolution || '10m',
                details: ev,
              });
            });
          }

          const assistantMsg: ChatMessage = {
            id: `asst_${Date.now()}`,

            role: 'assistant',
            content: result.answer || 'Analysis complete.',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            sources: sources.length > 0 ? sources : undefined,
            followUpSuggestions: result.follow_up_suggestions,
            geojson: result.geojson,
          };

          set((state) => ({
            messages: [...state.messages, assistantMsg],
            conversationId: result.conversation_id || state.conversationId,
            isAnalyzing: false,
            friendlyStatus: null,
          }));

          // Refresh sessions list
          get().fetchHistory();
        },
        onFailed: (errPayload) => {
          const errMsg: ChatMessage = {
            id: `asst_${Date.now()}`,

            role: 'assistant',
            content: errPayload?.answer || 'OrbitMind encountered an issue while analyzing this request.',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            error: errPayload?.errors?.[0],
          };
          set((state) => ({
            messages: [...state.messages, errMsg],
            isAnalyzing: false,
            friendlyStatus: null,
            errorMessage: errPayload?.errors?.[0] || 'Analysis could not be completed.',
          }));
        },
        onError: (err) => {
          const failMsg: ChatMessage = {
            id: `asst_${Date.now()}`,

            role: 'assistant',
            content: 'OrbitMind is temporarily unable to connect to the analysis engine. Please try again.',
            timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            error: err.message,
          };
          set((state) => ({
            messages: [...state.messages, failMsg],
            isAnalyzing: false,
            friendlyStatus: null,
            errorMessage: err.message,
          }));
        },
      });
    } catch (streamErr: any) {
      // Synchronous fallback if SSE connection fails
      try {
        set({ friendlyStatus: 'Synthesizing response...' });
        const result = await sendChat(payload);
        const assistantMsg: ChatMessage = {
          id: `asst_${Date.now()}`,

          role: 'assistant',
          content: result.answer || 'Analysis complete.',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          followUpSuggestions: result.follow_up_suggestions,
          geojson: result.geojson,
        };
        set((state) => ({
          messages: [...state.messages, assistantMsg],
          conversationId: result.conversation_id || state.conversationId,
          isAnalyzing: false,
          friendlyStatus: null,
        }));
        get().fetchHistory();
      } catch (fallbackErr: any) {
        set({
          isAnalyzing: false,
          friendlyStatus: null,
          errorMessage: 'OrbitMind is temporarily unable to complete this analysis.',
        });
      }
    }
  },
}));
