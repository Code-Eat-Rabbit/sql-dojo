import { useEffect, useRef, useState } from 'react'
import CodeMirror from '@uiw/react-codemirror'
import { sql } from '@codemirror/lang-sql'
import { executeSql, submitSql, getDraft, saveDraft } from '../api'
import type { SqlExecuteResult } from '../types'
import ResultTable from './ResultTable'

type Verdict = { correct: boolean; diffSummary: string | null }

export default function SQLWorkspace({
  problemId,
  gradable,
  onCorrect,
}: {
  problemId: string
  gradable: boolean
  onCorrect: () => void
}) {
  const [code, setCode] = useState('')
  const [result, setResult] = useState<SqlExecuteResult | null>(null)
  const [verdict, setVerdict] = useState<Verdict | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [offline, setOffline] = useState(false)
  const [busy, setBusy] = useState<'run' | 'submit' | null>(null)
  const debounceRef = useRef<number | null>(null)

  // 切题：回填草稿、清空状态
  useEffect(() => {
    setCode('')
    setResult(null)
    setVerdict(null)
    setError(null)
    getDraft(problemId)
      .then((d) => setCode(d.sql))
      .catch(() => {})
    return () => {
      if (debounceRef.current) window.clearTimeout(debounceRef.current)
    }
  }, [problemId])

  const handleChange = (value: string) => {
    setCode(value)
    if (debounceRef.current) window.clearTimeout(debounceRef.current)
    debounceRef.current = window.setTimeout(() => {
      saveDraft(problemId, value).catch(() => {})
    }, 1000)
  }

  const run = async () => {
    setBusy('run')
    try {
      const r = await executeSql(problemId, code)
      setResult(r)
      setVerdict(null)
      setError(null)
      setOffline(false)
    } catch (e) {
      const err = e as Error & { status?: number }
      setOffline(err.status === 503)
      setError(err.status === 503 ? null : err.message)
      setResult(null)
    } finally {
      setBusy(null)
    }
  }

  const submit = async () => {
    setBusy('submit')
    try {
      const v = await submitSql(problemId, code)
      setVerdict(v)
      setError(null)
      setOffline(false)
      if (v.correct) onCorrect()
    } catch (e) {
      const err = e as Error & { status?: number }
      setOffline(err.status === 503)
      setError(err.status === 503 ? null : err.message)
      setVerdict(null)
    } finally {
      setBusy(null)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      e.preventDefault()
      if (!busy && code.trim()) run()
    }
  }

  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wide mb-2">Your SQL</h3>

      {offline && (
        <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-3 mb-3 text-sm">
          MySQL 未启动，请先运行 <code className="font-mono">bash start.sh</code> 后重试
        </div>
      )}

      <div onKeyDown={handleKeyDown} className="border border-gray-200 rounded-lg overflow-hidden">
        <CodeMirror
          value={code}
          onChange={handleChange}
          extensions={[sql()]}
          height="160px"
          theme="light"
          placeholder="-- 在此编写 SQL，Ctrl/⌘ + Enter 运行"
        />
      </div>

      <div className="flex items-center gap-3 mt-3">
        <button
          onClick={run}
          disabled={busy !== null || !code.trim()}
          className="px-4 py-2 text-sm border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
        >
          {busy === 'run' ? '运行中…' : '运行'}
        </button>
        {gradable ? (
          <button
            onClick={submit}
            disabled={busy !== null || !code.trim()}
            className="px-4 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            {busy === 'submit' ? '判题中…' : '提交答案'}
          </button>
        ) : (
          <span className="text-xs text-gray-400">
            此题为 DDL/说明题，请在 DBeaver 等外部工具完成后手动标记
          </span>
        )}
        <span className="text-xs text-gray-400">Ctrl/⌘ + Enter 运行</span>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 mt-3 text-sm font-mono whitespace-pre-wrap">
          {error}
        </div>
      )}

      {verdict && (
        <div
          className={`rounded-lg p-3 mt-3 text-sm border ${
            verdict.correct
              ? 'bg-green-50 border-green-200 text-green-700'
              : 'bg-red-50 border-red-200 text-red-700'
          }`}
        >
          {verdict.correct ? '判定正确！请在弹窗中完成自评' : `判定不符：${verdict.diffSummary}`}
        </div>
      )}

      {result && (
        <div className="mt-3">
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <ResultTable
              columns={result.columns.map((c) => ({ name: c }))}
              rows={result.rows}
            />
          </div>
          <div className="text-xs text-gray-400 mt-1">
            {result.rowCount} rows · {result.elapsedMs} ms
            {result.truncated ? ' · 超过 500 行，仅展示前 500 行' : ''}
          </div>
        </div>
      )}
    </div>
  )
}
