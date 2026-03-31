import { useEffect, useRef } from 'react'
import { v4 as uuidv4 } from 'uuid'
import { useChatStore } from '../store/chatStore'
import { streamChat } from '../api/chatApi'
import MessageBubble from './MessageBubble'
import InputBar from './InputBar'
import ThinkingIndicator from './ThinkingIndicator'

export default function ChatWindow() {
  const {
    messages, sessionId, userId,
    isLoading, isStreaming,
    addMessage, appendChunk, setStreaming,
    setLoading, setIsStreaming,
    loadSessions,
  } = useChatStore()

  const bottomRef = useRef(null)

  // Auto-scroll to bottom on new messages or chunks
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (text) => {
    if (!sessionId) {
      alert('Please create or select a session first.')
      return
    }

    // Add user message immediately
    addMessage({
      id: uuidv4(),
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    })

    // Create placeholder for assistant reply
    const assistantId = uuidv4()
    addMessage({
      id: assistantId,
      role: 'assistant',
      content: '',
      streaming: true,
      timestamp: new Date().toISOString(),
    })

    setLoading(true)
    setIsStreaming(true)

    await streamChat(
      sessionId,
      userId,
      text,

      // onChunk — append each token to the assistant message
      (chunk) => {
        setLoading(false)
        appendChunk(assistantId, chunk)
      },

      // onDone — streaming finished
      () => {
        setStreaming(assistantId, false)
        setIsStreaming(false)
        setLoading(false)
        loadSessions() // refresh session list to update last_active
      },

      // onError — show error in the chat bubble
      (err) => {
        const msg = err.code === 429
          ? 'Rate limit reached. Please wait a moment and try again.'
          : `Error: ${err.error || 'Something went wrong'}`
        appendChunk(assistantId, msg)
        setStreaming(assistantId, false)
        setIsStreaming(false)
        setLoading(false)
      }
    )
  }

  return (
    <div className="flex flex-col h-full flex-1 min-w-0">

      {/* Header */}
      <div className="border-b border-[#2a2a2a] px-6 py-4 bg-[#0f0f0f]">
        <h1 className="text-[#e5e5e5] font-semibold">
          {sessionId ? 'Chat' : 'Select or create a session'}
        </h1>
        <p className="text-[#555] text-xs mt-0.5">
          Powered by LangGraph · Multi-agent · Long-term memory
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-2xl bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center mb-4">
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="1.5">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h2 className="text-[#e5e5e5] font-semibold text-lg mb-2">Start a conversation</h2>
            <p className="text-[#555] text-sm max-w-sm">
              Ask anything. The AI remembers you across sessions and can search the web, do math, and check the weather.
            </p>
          </div>
        )}

        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}

        {isLoading && <ThinkingIndicator />}
        <div ref={bottomRef} />
      </div>

      <InputBar onSend={handleSend} disabled={isLoading || isStreaming} />
    </div>
  )
}