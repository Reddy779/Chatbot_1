import { create } from 'zustand'
import { v4 as uuidv4 } from 'uuid'
import { getSessions, getFacts, getSummaries, deleteFact, createSession } from '../api/chatApi'


const savedUserId    = localStorage.getItem('userId')    || (() => { const id = uuidv4(); localStorage.setItem('userId', id); return id })()
const savedSessionId = localStorage.getItem('sessionId') || null

export const useChatStore = create((set, get) => ({
  // Identity 
  userId:    savedUserId,
  sessionId: savedSessionId,

  // Messages 
  messages:  [],

  // Sessions 
  sessions:  [],

  // Memory 
  userFacts:  [],
  summaries:  [],

  // UI State 
  isLoading:   false,
  isStreaming: false,
  toast:       null,

  // Actions 

  setSessionId: (id) => {
    localStorage.setItem('sessionId', id)
    set({ sessionId: id, messages: [] })
  },

  addMessage: (msg) =>
    set((state) => ({ messages: [...state.messages, msg] })),

  appendChunk: (id, chunk) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, content: m.content + chunk } : m
      ),
    })),

  setStreaming: (id, streaming) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, streaming } : m
      ),
    })),

  setLoading: (v) => set({ isLoading: v }),
  setIsStreaming: (v) => set({ isStreaming: v }),

  showToast: (message, type = 'success') => {
    set({ toast: { message, type } })
    setTimeout(() => set({ toast: null }), 3000)
  },

  // API Actions 

  loadSessions: async () => {
    const { userId } = get()
    try {
      const { data } = await getSessions(userId)
      set({ sessions: data })
    } catch {
      // silently fail 
    }
  },

  createNewSession: async () => {
    const { userId, showToast } = get()
    try {
      const { data } = await createSession(userId)
      set((state) => ({ sessions: [data, ...state.sessions] }))
      get().setSessionId(data.session_id)
      showToast('New chat started')
    } catch {
      showToast('Failed to create session', 'error')
    }
  },

  loadFacts: async () => {
    const { userId } = get()
    try {
      const { data } = await getFacts(userId)
      set({ userFacts: data })
    } catch {
      // silently fail
    }
  },

  loadSummaries: async () => {
    const { userId } = get()
    try {
      const { data } = await getSummaries(userId)
      set({ summaries: data })
    } catch {
      // silently fail
    }
  },

  deleteFact: async (factId) => {
    const { showToast } = get()
    try {
      await deleteFact(factId)
      set((state) => ({
        userFacts: state.userFacts.filter((f) => f.id !== factId),
      }))
      showToast('Fact deleted')
    } catch {
      showToast('Failed to delete fact', 'error')
    }
  },
}))