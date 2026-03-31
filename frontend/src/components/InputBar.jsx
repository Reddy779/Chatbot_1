import { useState, useRef, useEffect } from 'react'

export default function InputBar({ onSend, disabled }) {
  const [text, setText] = useState('')
  const textareaRef = useRef(null)

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 160) + 'px'
  }, [text])

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed || disabled) return
    onSend(trimmed)
    setText('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const charCount = text.length
  const isNearLimit = charCount > 3500

  return (
    <div className="border-t border-[#2a2a2a] bg-[#0f0f0f] p-4">
      <div className="flex items-end gap-3 bg-[#1a1a1a] border border-[#2a2a2a] rounded-2xl px-4 py-3 focus-within:border-indigo-500 transition-colors">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Message the AI... (Shift+Enter for new line)"
          rows={1}
          className="flex-1 bg-transparent text-[#e5e5e5] placeholder-[#555] resize-none outline-none text-sm leading-relaxed disabled:opacity-50"
          style={{ maxHeight: '160px' }}
        />

        <div className="flex items-center gap-2 shrink-0">
          {/* Character count warning */}
          {isNearLimit && (
            <span className="text-xs text-orange-400">{charCount}/4000</span>
          )}

          {/* Send button */}
          <button
            onClick={handleSend}
            disabled={disabled || !text.trim()}
            className="w-8 h-8 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
      </div>

      <p className="text-center text-[#444] text-xs mt-2">
        Enter to send · Shift+Enter for new line
      </p>
    </div>
  )
}