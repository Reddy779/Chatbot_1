import { useEffect } from 'react'
import { useChatStore } from '../store/chatStore'

function timeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime()
  const mins = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}

export default function SessionSidebar() {
  const {
    sessions, sessionId, userId,
    loadSessions, setSessionId, createNewSession,
  } = useChatStore()

  useEffect(() => {
    loadSessions()
  }, [])

  return (
    <div className="w-64 shrink-0 bg-[#0a0a0a] border-r border-[#2a2a2a] flex flex-col h-full">

      {/* Header */}
      <div className="p-4 border-b border-[#2a2a2a]">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-7 h-7 rounded-lg bg-indigo-600 flex items-center justify-center">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
            </svg>
          </div>
          <span className="text-[#e5e5e5] font-semibold text-sm">DR Chatbot</span>
        </div>

        {/* New Chat Button */}
        <button
          onClick={createNewSession}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-medium transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          New Chat
        </button>
      </div>

      {/* Sessions list */}
      <div className="flex-1 overflow-y-auto p-2">
        {sessions.length === 0 ? (
          <p className="text-[#444] text-xs text-center mt-8 px-4">
            No sessions yet. Start a new chat!
          </p>
        ) : (
          sessions.map((s) => (
            <button
              key={s.session_id}
              onClick={() => setSessionId(s.session_id)}
              className={`w-full text-left px-3 py-2.5 rounded-xl mb-1 transition-colors group ${
                sessionId === s.session_id
                  ? 'bg-[#1e1e1e] border border-indigo-500/40'
                  : 'hover:bg-[#1a1a1a] border border-transparent'
              }`}
            >
              <p className={`text-sm truncate ${sessionId === s.session_id ? 'text-[#e5e5e5]' : 'text-[#aaa]'}`}>
                {s.title || 'Untitled chat'}
              </p>
              <p className="text-[#555] text-xs mt-0.5">
                {s.last_active ? timeAgo(s.last_active) : ''}
              </p>
            </button>
          ))
        )}
      </div>

      {/* User ID footer */}
      <div className="p-3 border-t border-[#2a2a2a]">
        <p className="text-[#444] text-xs truncate">
          User: {userId?.slice(0, 16)}...
        </p>
      </div>
    </div>
  )
}