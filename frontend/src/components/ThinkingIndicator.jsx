export default function ThinkingIndicator() {
  return (
    <div className="flex items-start gap-3 mb-4">
      {/* Agent avatar */}
      <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-white text-xs font-bold shrink-0">
        AI
      </div>

      {/* Thinking bubble */}
      <div className="bg-[#1e1e1e] border border-[#2a2a2a] rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex items-center gap-1">
          <span className="text-[#888] text-sm mr-2">Thinking</span>
          <span className="w-2 h-2 rounded-full bg-indigo-400 dot-1 inline-block" />
          <span className="w-2 h-2 rounded-full bg-indigo-400 dot-2 inline-block" />
          <span className="w-2 h-2 rounded-full bg-indigo-400 dot-3 inline-block" />
        </div>
      </div>
    </div>
  )
}