function formatTime(date) {
  const d = new Date(date)
  const now = new Date()
  const isToday = d.toDateString() === now.toDateString()
  if (isToday) return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

function renderContent(content) {
  // Split by code blocks first
  const parts = content.split(/(```[\s\S]*?```)/g)
  return parts.map((part, i) => {
    if (part.startsWith('```')) {
      const code = part.replace(/^```[\w]*\n?/, '').replace(/```$/, '')
      return (
        <pre key={i} className="bg-[#0f0f0f] border border-[#2a2a2a] rounded-lg p-3 mt-2 mb-2 overflow-x-auto text-sm text-green-400 font-mono whitespace-pre-wrap">
          {code}
        </pre>
      )
    }
    // Render bold text
    const boldParts = part.split(/(\*\*.*?\*\*)/g)
    return (
      <span key={i}>
        {boldParts.map((bp, j) =>
          bp.startsWith('**') ? (
            <strong key={j} className="font-semibold">
              {bp.slice(2, -2)}
            </strong>
          ) : (
            <span key={j} style={{ whiteSpace: 'pre-wrap' }}>{bp}</span>
          )
        )}
      </span>
    )
  })
}

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user'

  return (
    <div className={`flex items-start gap-3 mb-4 ${isUser ? 'flex-row-reverse' : ''}`}>

      {/* Avatar */}
      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-xs font-bold shrink-0 ${isUser ? 'bg-violet-600' : 'bg-indigo-600'}`}>
        {isUser ? 'You' : 'AI'}
      </div>

      {/* Bubble */}
      <div className={`max-w-[72%] ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${
          isUser
            ? 'bg-violet-600 text-white rounded-tr-sm'
            : 'bg-[#1e1e1e] border border-[#2a2a2a] text-[#e5e5e5] rounded-tl-sm'
        }`}>
          {renderContent(message.content)}

          {/* Blinking cursor while streaming */}
          {message.streaming && (
            <span className="inline-block w-0.5 h-4 bg-indigo-400 ml-0.5 cursor-blink align-middle" />
          )}
        </div>

        {/* Timestamp */}
        {message.timestamp && (
          <span className="text-[#555] text-xs mt-1 px-1">
            {formatTime(message.timestamp)}
          </span>
        )}
      </div>
    </div>
  )
}