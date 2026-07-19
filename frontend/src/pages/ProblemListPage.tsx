import { useEffect, useState, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import ReactMarkdown from 'react-markdown'
import { getProblems, getProblemDetail, getProblemTables, completeProblem } from '../api'
import type { ProblemBrief, ProblemDetail, TableInfo } from '../types'

/* ── Sub-components ── */

function StarDisplay({ level, max = 5 }: { level: number; max?: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: max }, (_, i) => (
        <svg
          key={i}
          className={`w-4 h-4 ${i < level ? 'text-yellow-400' : 'text-gray-300'}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </div>
  )
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: 'bg-green-500',
    in_progress: 'bg-yellow-400',
    not_started: 'bg-gray-300',
  }
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${colors[status] || 'bg-gray-300'}`} />
}

/* ── Rating Modal ── */

function RatingModal({
  open,
  onClose,
  onSubmit,
}: {
  open: boolean
  onClose: () => void
  onSubmit: (stars: number, notes: string) => void
}) {
  const [stars, setStars] = useState(3)
  const [notes, setNotes] = useState('')

  if (!open) return null

  const handleSubmit = () => {
    onSubmit(stars, notes)
    setStars(3)
    setNotes('')
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Rate Your Mastery</h3>

        <div className="flex gap-2 mb-4 justify-center">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              onClick={() => setStars(n)}
              className="p-1 transition-transform hover:scale-110"
            >
              <svg
                className={`w-8 h-8 ${n <= stars ? 'text-yellow-400' : 'text-gray-300'}`}
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </button>
          ))}
          <span className="ml-2 text-sm text-gray-500 self-center">
            {stars} / 5
          </span>
        </div>

        <textarea
          className="w-full border border-gray-300 rounded-lg p-3 text-sm mb-4 resize-none focus:outline-none focus:ring-2 focus:ring-green-400"
          rows={3}
          placeholder="Optional notes..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />

        <div className="flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            Complete
          </button>
        </div>
      </div>
    </div>
  )
}

/* ── Main Page ── */

export default function ProblemListPage() {
  const { id: categoryId } = useParams<{ id: string }>()

  const [problems, setProblems] = useState<ProblemBrief[]>([])
  const [categoryName, setCategoryName] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<ProblemDetail | null>(null)
  const [tables, setTables] = useState<TableInfo[]>([])
  const [dbConnection, setDbConnection] = useState('')
  const [loadingList, setLoadingList] = useState(true)
  const [loadingDetail, setLoadingDetail] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [showAnswer, setShowAnswer] = useState(false)
  const [showRating, setShowRating] = useState(false)
  const [copied, setCopied] = useState(false)

  // Load problem list
  useEffect(() => {
    if (!categoryId) return
    setLoadingList(true)
    getProblems(categoryId)
      .then((data) => {
        setProblems(data.problems)
        setCategoryName(data.category?.name || '')
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoadingList(false))
  }, [categoryId])

  // Load problem detail
  const loadDetail = useCallback(async (id: string) => {
    setLoadingDetail(true)
    setShowAnswer(false)
    try {
      const [d, t] = await Promise.all([getProblemDetail(id), getProblemTables(id)])
      setDetail(d)
      setTables(t.tables)
      setDbConnection(t.db_connection)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load problem')
    } finally {
      setLoadingDetail(false)
    }
  }, [])

  // Select a problem
  const handleSelect = (id: string) => {
    setSelectedId(id)
    loadDetail(id)
  }

  // Complete with rating
  const handleComplete = async (stars: number, _notes: string) => {
    if (!selectedId) return

    // Optimistic update
    setDetail((prev) =>
      prev
        ? {
            ...prev,
            progress: {
              status: 'completed',
              completed_count: (prev.progress?.completed_count || 0) + 1,
              mastery_level: Math.max(prev.progress?.mastery_level || 0, stars),
              last_practiced_at: new Date().toISOString(),
            },
          }
        : prev
    )

    // Also update problems list optimistically
    setProblems((prev) =>
      prev.map((p) =>
        p.id === selectedId
          ? {
              ...p,
              progress: {
                status: 'completed',
                completed_count: (p.progress?.completed_count || 0) + 1,
                mastery_level: Math.max(p.progress?.mastery_level || 0, stars),
                last_practiced_at: new Date().toISOString(),
              },
            }
          : p
      )
    )

    try {
      await completeProblem(selectedId, stars)
      // Reload detail to get server-computed values
      const d = await getProblemDetail(selectedId)
      setDetail(d)
    } catch {
      // Revert on failure — reload from server
      if (selectedId) loadDetail(selectedId)
    }
  }

  const handleCopy = () => {
    if (!dbConnection) return
    navigator.clipboard.writeText(dbConnection).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  if (loadingList) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-gray-900" />
      </div>
    )
  }

  if (error && problems.length === 0) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
        {error}
      </div>
    )
  }

  const progress = detail?.progress

  return (
    <div className="flex gap-6 h-[calc(100vh-130px)]">
      {/* ── Left Sidebar ── */}
      <aside className="w-[300px] flex-shrink-0 bg-white rounded-lg shadow-sm overflow-hidden flex flex-col">
        <div className="p-4 border-b border-gray-100 bg-gray-50">
          <h2 className="font-semibold text-gray-800 truncate">{categoryName || 'Problems'}</h2>
          <p className="text-xs text-gray-500 mt-1">{problems.length} problems</p>
        </div>
        <ul className="flex-1 overflow-y-auto custom-scrollbar">
          {problems.map((p) => {
            const isSelected = p.id === selectedId
            const status = p.progress?.status || 'not_started'
            return (
              <li
                key={p.id}
                onClick={() => handleSelect(p.id)}
                className={`px-4 py-3 border-b border-gray-50 cursor-pointer transition-colors flex items-start gap-3 ${
                  isSelected ? 'bg-green-50 border-l-4 border-l-green-500' : 'hover:bg-gray-50 border-l-4 border-l-transparent'
                }`}
              >
                <span className="mt-1.5 flex-shrink-0">
                  <StatusDot status={status} />
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-gray-800 truncate">{p.title}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <StarDisplay level={p.difficulty} />
                    {p.progress && p.progress.completed_count > 0 && (
                      <span className="text-xs text-gray-400">
                        {p.progress.completed_count}x
                      </span>
                    )}
                  </div>
                </div>
              </li>
            )
          })}
        </ul>
      </aside>

      {/* ── Right Panel ── */}
      <section className="flex-1 bg-white rounded-lg shadow-sm overflow-y-auto custom-scrollbar p-6">
        {!selectedId && (
          <div className="flex items-center justify-center h-full text-gray-400">
            <p>Select a problem from the sidebar to begin.</p>
          </div>
        )}

        {loadingDetail && (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900" />
          </div>
        )}

        {detail && !loadingDetail && (
          <div>
            {/* Title + Tags */}
            <h1 className="text-2xl font-bold text-gray-900 mb-1">{detail.title}</h1>
            <div className="flex items-center gap-3 mb-4 text-sm text-gray-500">
              <StarDisplay level={detail.difficulty} />
              <span>Difficulty {detail.difficulty}/5</span>
              {detail.tags.map((tag) => (
                <span key={tag} className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">
                  {tag}
                </span>
              ))}
            </div>

            {/* DbConnectionInfo */}
            <div className="bg-gray-50 rounded-lg p-4 mb-6 border border-gray-200">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs text-gray-500 uppercase tracking-wide">Database</span>
                  <p className="text-sm font-mono text-gray-700 mt-0.5">{detail.db_file}</p>
                </div>
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-white border border-gray-300 rounded-md hover:bg-gray-100 transition-colors"
                >
                  {copied ? (
                    <>
                      <svg className="w-3.5 h-3.5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Copied
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                      Copy connection string
                    </>
                  )}
                </button>
              </div>
              {dbConnection && (
                <p className="text-xs font-mono text-gray-400 mt-2 truncate">{dbConnection}</p>
              )}
            </div>

            {/* Description */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Description</h3>
              <div className="prose text-sm text-gray-700">
                <ReactMarkdown>{detail.description}</ReactMarkdown>
              </div>
            </div>

            {/* Table Schema */}
            {tables.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-3">Table Schema</h3>
                {tables.map((table) => (
                  <div key={table.name} className="mb-4 border border-gray-200 rounded-lg overflow-hidden">
                    <div className="bg-gray-100 px-4 py-2 font-medium text-sm text-gray-700">
                      {table.name}
                      <span className="ml-2 text-xs text-gray-400 font-normal">
                        ({table.row_count} rows)
                      </span>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="bg-gray-50 text-left text-xs text-gray-500 uppercase">
                            {table.columns.map((col) => (
                              <th key={col.name} className="px-4 py-2 font-medium">
                                {col.name}
                                <span className="ml-1 text-gray-400 font-normal lowercase">{col.type}</span>
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {table.sample_rows.map((row, ri) => (
                            <tr key={ri} className="border-t border-gray-100 hover:bg-gray-50">
                              {table.columns.map((col) => (
                                <td key={col.name} className="px-4 py-2 font-mono text-xs text-gray-600">
                                  {String(row[col.name] ?? 'NULL')}
                                </td>
                              ))}
                            </tr>
                          ))}
                          {table.sample_rows.length === 0 && (
                            <tr>
                              <td colSpan={table.columns.length} className="px-4 py-4 text-center text-gray-400 text-xs">
                                No sample data
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Reference Answer */}
            {detail.reference_sql && (
              <div className="mb-6">
                <button
                  onClick={() => setShowAnswer(!showAnswer)}
                  className="flex items-center gap-2 text-sm font-semibold text-gray-700 uppercase tracking-wide hover:text-green-600 transition-colors"
                >
                  <svg
                    className={`w-4 h-4 transition-transform ${showAnswer ? 'rotate-90' : ''}`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                  Reference Answer
                </button>
                {showAnswer && (
                  <div className="mt-2 bg-gray-900 text-green-300 rounded-lg p-4 overflow-x-auto">
                    <pre className="text-sm font-mono whitespace-pre-wrap">{detail.reference_sql}</pre>
                  </div>
                )}
              </div>
            )}

            {/* Hints */}
            {detail.hints.length > 0 && (
              <div className="mb-6">
                <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Hints</h3>
                <ul className="space-y-1">
                  {detail.hints.map((hint, i) => (
                    <li key={i} className="text-sm text-gray-600 flex gap-2">
                      <span className="text-yellow-500">💡</span>
                      {hint}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Progress Panel */}
            <div className="border-t border-gray-200 pt-6 mt-6">
              <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-4">Your Progress</h3>
              <div className="flex items-center gap-6 flex-wrap">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-500">Mastery:</span>
                  <StarDisplay level={progress?.mastery_level || 0} />
                  <span className="text-xs text-gray-400">
                    {progress?.mastery_level || 0}/5
                  </span>
                </div>
                <div>
                  <span className="text-sm text-gray-500">Completed: </span>
                  <span className="text-sm font-semibold text-gray-800">
                    {progress?.completed_count || 0} times
                  </span>
                </div>
                {progress?.last_practiced_at && (
                  <div>
                    <span className="text-sm text-gray-500">Last practiced: </span>
                    <span className="text-sm text-gray-700">
                      {new Date(progress.last_practiced_at).toLocaleDateString()}
                    </span>
                  </div>
                )}
              </div>
              <button
                onClick={() => setShowRating(true)}
                className="mt-4 px-6 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
              >
                Mark as Complete
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Rating Modal */}
      <RatingModal open={showRating} onClose={() => setShowRating(false)} onSubmit={handleComplete} />
    </div>
  )
}
