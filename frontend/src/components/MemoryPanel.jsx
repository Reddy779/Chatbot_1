import { useEffect, useState } from 'react'
import { useChatStore } from '../store/chatStore'

export default function MemoryPanel() {
  const { userFacts, summaries, loadFacts, loadSummaries, deleteFact } = useChatStore()
  const [activeTab, setActiveTab] = useState('facts')

  useEffect(() => {
    loadFacts()
    loadSummaries()
  }, [])

  return (
    <div className="w-72 shrink-0 bg-[#0a0a0a] border-l border-[#2a2a2a] flex flex-col h-full">

      {/* Header */}
      <div className="p-4 border-b border-[#2a2a2a]">
        <div className="flex items-center gap-2">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6366f1" strokeWidth="2">
            <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z"/>
            <path d="M12 6v6l4 2"/>
          </svg>
          <h2 className="text-[#e5e5e5] font-semibold text-sm">Memory</h2>
        </div>
        <p className="text-[#555] text-xs mt-1">What the AI knows about you</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#2a2a2a]">
        <button
          onClick={() => setActiveTab('facts')}
          className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
            activeTab === 'facts'
              ? 'text-indigo-400 border-b-2 border-indigo-500'
              : 'text-[#555] hover:text-[#aaa]'
          }`}
        >
          Facts ({userFacts.length})
        </button>
        <button
          onClick={() => setActiveTab('summaries')}
          className={`flex-1 py-2.5 text-xs font-medium transition-colors ${
            activeTab === 'summaries'
              ? 'text-indigo-400 border-b-2 border-indigo-500'
              : 'text-[#555] hover:text-[#aaa]'
          }`}
        >
          Summaries ({summaries.length})
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-3">

        {/* Facts tab */}
        {activeTab === 'facts' && (
          <div>
            {userFacts.length === 0 ? (
              <div className="text-center mt-8">
                <p className="text-[#444] text-xs">No facts learned yet.</p>
                <p className="text-[#333] text-xs mt-1">
                  Tell the AI your name, preferences, or interests.
                </p>
              </div>
            ) : (
              userFacts.map((fact) => (
                <div
                  key={fact.id}
                  className="flex items-start gap-2 py-2 px-3 rounded-xl mb-1 bg-[#141414] border border-[#2a2a2a] group"
                >
                  <div className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0" />
                  <p className="text-[#ccc] text-xs flex-1 leading-relaxed">{fact.fact}</p>
                  <button
                    onClick={() => deleteFact(fact.id)}
                    className="opacity-0 group-hover:opacity-100 text-[#555] hover:text-red-400 transition-all shrink-0"
                    title="Delete this fact"
                  >
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="3 6 5 6 21 6"/>
                      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/>
                      <path d="M10 11v6M14 11v6"/>
                    </svg>
                  </button>
                </div>
              ))
            )}
          </div>
        )}

        {/* Summaries tab */}
        {activeTab === 'summaries' && (
          <div>
            {summaries.length === 0 ? (
              <div className="text-center mt-8">
                <p className="text-[#444] text-xs">No summaries yet.</p>
                <p className="text-[#333] text-xs mt-1">
                  Summaries are created after 30+ messages in a session.
                </p>
              </div>
            ) : (
              summaries.map((s) => (
                <div
                  key={s.id}
                  className="mb-3 p-3 rounded-xl bg-[#141414] border border-[#2a2a2a]"
                >
                  <p className="text-[#555] text-xs mb-1.5">
                    {new Date(s.created_at).toLocaleDateString([], {
                      month: 'short', day: 'numeric', year: 'numeric'
                    })}
                  </p>
                  <p className="text-[#aaa] text-xs leading-relaxed">{s.content}</p>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Refresh button */}
      <div className="p-3 border-t border-[#2a2a2a]">
        <button
          onClick={() => { loadFacts(); loadSummaries() }}
          className="w-full py-2 rounded-xl text-xs text-[#555] hover:text-[#aaa] hover:bg-[#1a1a1a] transition-colors"
        >
          Refresh memory
        </button>
      </div>
    </div>
  )
}