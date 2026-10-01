import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

export default function KnowledgePanel({
  title,
  knowledge,
}: {
  title: string
  knowledge: string
}) {
  const [open, setOpen] = useState(true)

  if (!knowledge) return null

  return (
    <div className="bg-white rounded-lg shadow-sm mb-4 flex-shrink-0">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-gray-50 rounded-t-lg transition-colors"
      >
        <span className="text-sm font-semibold text-gray-700">📖 知识点：{title}</span>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform ${open ? 'rotate-90' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>
      {open && (
        <div className="px-4 pb-4 pt-3 border-t border-gray-100 prose prose-sm max-w-none text-sm text-gray-700">
          <ReactMarkdown>{knowledge}</ReactMarkdown>
        </div>
      )}
    </div>
  )
}
