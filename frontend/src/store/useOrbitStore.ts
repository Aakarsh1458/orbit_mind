import { create } from 'zustand';
import { AIStatusResponse, HealthResponse, ImageryItem } from '../types/api';
import { ChatResponse, OrchestrationStage, OrchestrationStep } from '../types/orchestration';
import { getAiStatus, getHealth } from '../api/modelsApi';
import { listImagery } from '../api/imageryApi';
import { streamChat, sendChat } from '../api/chatApi';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  imagery_ids?: string[];
  task?: string;
  model?: string;
  confidence?: number;
  timestamp: string;
  responsePayload?: ChatResponse;
}

interface OrbitState {
  // System Telemetry
  health: HealthResponse | null;
  aiStatus: AIStatusResponse | null;
  imageryList: ImageryItem[];
  selectedImageryIds: string[];
  activeImageryId: string | null;
  
  // Active Conversation & Execution
  conversationId: string | null;
  messages: ChatMessage[];
  isExecuting: boolean;
  activeStage: OrchestrationStage | null;
  executionSteps: OrchestrationStep[];
  currentResult: ChatResponse | null;
  lastError: string | null;

  // Actions
  fetchSystemStatus: () => Promise<void>;
  fetchImagery: () => Promise<void>;
  setSelectedImageryIds: (ids: string[]) => void;
  toggleImagerySelection: (id: string) => void;
  setActiveImageryId: (id: string | null) => void;
  chooseImage: (id: string) => void;
  choosePairForComparison: (id1: string, id2: string) => void;
  setConversationId: (id: string | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  addMessage: (msg: ChatMessage) => void;
  executePrompt: (prompt: string, useStreaming?: boolean) => Promise<void>;
  resetExecution: () => void;
  setCurrentResult: (res: ChatResponse | null) => void;
}

export const useOrbitStore = create<OrbitState>((set, get) => ({
  health: null,
  aiStatus: null,
  imageryList: [],
  selectedImageryIds: [],
  activeImageryId: null,
  conversationId: null,
  messages: [],
  isExecuting: false,
  activeStage: null,
  executionSteps: [],
  currentResult: null,
  lastError: null,

  fetchSystemStatus: async () => {
    try {
      const [h, s] = await Promise.allSettled([getHealth(), getAiStatus()]);
      set({
        health: h.status === 'fulfilled' ? h.value : null,
        aiStatus: s.status === 'fulfilled' ? s.value : null,
      });
    } catch (e: any) {
      console.error('Failed to fetch system status:', e);
    }
  },

  fetchImagery: async () => {
    try {
      const res = await listImagery(50, 0);
      set({ imageryList: res.items || [] });
      // If none selected and items exist, select up to 2 by default
      const currentSelected = get().selectedImageryIds;
      if (currentSelected.length === 0 && res.items.length > 0) {
        const initial = res.items.slice(0, 2).map((i) => i.id);
        set({ selectedImageryIds: initial, activeImageryId: initial[0] });
      } else if (!get().activeImageryId && currentSelected.length > 0) {
        set({ activeImageryId: currentSelected[0] });
      }
    } catch (e: any) {
      console.warn('Could not load imagery list:', e);
    }
  },

  setSelectedImageryIds: (ids) => {
    set({
      selectedImageryIds: ids,
      activeImageryId: ids.length > 0 ? (ids.includes(get().activeImageryId || '') ? get().activeImageryId : ids[0]) : null,
    });
  },

  toggleImagerySelection: (id) => {
    const current = get().selectedImageryIds;
    if (current.includes(id)) {
      const updated = current.filter((i) => i !== id);
      set({
        selectedImageryIds: updated,
        activeImageryId: get().activeImageryId === id ? (updated[0] || null) : get().activeImageryId,
      });
    } else {
      const updated = [...current, id];
      set({
        selectedImageryIds: updated,
        activeImageryId: id,
      });
    }
  },

  setActiveImageryId: (id) => set({ activeImageryId: id }),

  chooseImage: (id) => {
    const current = get().selectedImageryIds;
    const updated = current.includes(id) ? current : [...current, id];
    set({
      selectedImageryIds: updated,
      activeImageryId: id,
    });
  },

  choosePairForComparison: (id1, id2) => {
    const pair = [id1, id2].filter(Boolean);
    set({
      selectedImageryIds: pair,
      activeImageryId: id1,
    });
  },

  setConversationId: (id) => set({ conversationId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setCurrentResult: (res) => set({ currentResult: res }),

  resetExecution: () =>
    set({
      isExecuting: false,
      activeStage: null,
      executionSteps: [],
      lastError: null,
    }),

  executePrompt: async (prompt: string, useStreaming: boolean = true) => {
    const { conversationId, selectedImageryIds, addMessage } = get();
    const userMsgId = `user_${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: prompt,
      imagery_ids: selectedImageryIds,
      timestamp: new Date().toLocaleTimeString(),
    };
    addMessage(userMsg);

    set({
      isExecuting: true,
      activeStage: 'planning',
      executionSteps: [
        {
          step: 1,
          stage: 'planning',
          action: 'Initializing task planning & intent classification',
          status: 'running',
          duration_ms: 0,
        },
      ],
      lastError: null,
    });

    const payload = {
      message: prompt,
      conversation_id: conversationId,
      imagery_ids: selectedImageryIds,
    };

    if (useStreaming) {
      const startTime = performance.now();
      let stepCount = 1;

      await streamChat(payload, {
        onStatus: (stage) => {
          stepCount++;
          const elapsed = Math.round(performance.now() - startTime);
          set((state) => {
            const updatedSteps = state.executionSteps.map((s) => ({
              ...s,
              status: 'completed' as const,
            }));
            return {
              activeStage: stage,
              executionSteps: [
                ...updatedSteps,
                {
                  step: stepCount,
                  stage,
                  action: `Executing ${stage.replace('_', ' ').toUpperCase()}`,
                  status: 'running',
                  duration_ms: elapsed,
                },
              ],
            };
          });
        },
        onCompleted: (result) => {
          const finalDuration = Math.round(performance.now() - startTime);
          set((state) => ({
            isExecuting: false,
            activeStage: 'completed',
            currentResult: result,
            conversationId: result.conversation_id || state.conversationId,
            executionSteps: state.executionSteps.map((s) => ({
              ...s,
              status: 'completed' as const,
            })),
          }));

          const assistantMsg: ChatMessage = {
            id: `asst_${Date.now()}`,
            role: 'assistant',
            content: result.answer || 'Analysis complete.',
            task: result.analysis?.task,
            model: result.analysis?.model,
            timestamp: new Date().toLocaleTimeString(),
            responsePayload: result,
          };
          addMessage(assistantMsg);
        },
        onFailed: (errPayload) => {
          set({
            isExecuting: false,
            activeStage: 'failed',
            lastError: errPayload?.answer || errPayload?.errors?.[0] || 'Analysis failed.',
          });
          const failMsg: ChatMessage = {
            id: `asst_${Date.now()}`,
            role: 'assistant',
            content: errPayload?.answer || 'Analysis could not be completed.',
            task: errPayload?.analysis?.task,
            timestamp: new Date().toLocaleTimeString(),
            responsePayload: errPayload,
          };
          addMessage(failMsg);
        },
        onError: (err) => {
          set({
            isExecuting: false,
            activeStage: 'failed',
            lastError: err.message,
          });
        },
      });
    } else {
      // Synchronous fallback
      try {
        const result = await sendChat(payload);
        set((state) => ({
          isExecuting: false,
          activeStage: 'completed',
          currentResult: result,
          conversationId: result.conversation_id || state.conversationId,
        }));
        const assistantMsg: ChatMessage = {
          id: `asst_${Date.now()}`,
          role: 'assistant',
          content: result.answer || 'Analysis completed.',
          task: result.analysis?.task,
          model: result.analysis?.model,
          timestamp: new Date().toLocaleTimeString(),
          responsePayload: result,
        };
        addMessage(assistantMsg);
      } catch (err: any) {
        set({
          isExecuting: false,
          activeStage: 'failed',
          lastError: err.message,
        });
      }
    }
  },
}));
