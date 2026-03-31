import { useEffect } from 'react'
import { useChatStore } from './store/chatStore'
import SessionSidebar from './components/SessionSidebar'
import ChatWindow from './components/ChatWindow'
import MemoryPanel from './components/MemoryPanel'

function Toast() {
  const toast = useChatStore((s) => s.toast)
  if (!toast) return null
  return (
    <div className={`fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-2.5 rounded-xl text-sm font-medium shadow-lg z-50 transition-all ${
      toast.type === 'error'
        ? 'bg-red-600 text-white'
        : 'bg-indigo-600 text-white'
    }`}>
      {toast.message}
    </div>
  )
}

export default function App() {
  const { loadSessions, loadFacts, createNewSession, sessionId } = useChatStore()

  useEffect(() => {
    loadSessions()
    loadFacts()
    // Auto-create a session if none exists
    if (!sessionId) createNewSession()
  }, [])

  return (
    <div className="flex h-screen bg-[#0f0f0f] overflow-hidden">
      <SessionSidebar />
      <ChatWindow />
      <MemoryPanel />
      <Toast />
    </div>
  )
}