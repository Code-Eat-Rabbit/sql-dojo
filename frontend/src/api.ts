import type {
  CategoryListResponse,
  ProblemBrief,
  ProblemDetail,
  TablesResponse,
  CompleteResponse,
  ProgressUpdateResponse,
  SqlExecuteResult,
  SqlSubmitResult,
  DraftResponse,
} from './types'

const BASE = '/api'

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options)
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`API error ${res.status}: ${text}`)
  }
  return res.json()
}

export function getCategories(): Promise<CategoryListResponse> {
  return fetchJson<CategoryListResponse>(`${BASE}/categories`)
}

export function getProblems(categoryId: string): Promise<{
  category: { id: string; name: string; db_file: string; order: number; knowledge: string } | null
  problems: ProblemBrief[]
  stats: { total: number; completed: number }
}> {
  return fetchJson(`${BASE}/problems?category_id=${encodeURIComponent(categoryId)}`)
}

export function getProblemDetail(id: string): Promise<ProblemDetail> {
  return fetchJson<ProblemDetail>(`${BASE}/problems/${encodeURIComponent(id)}`)
}

export function getProblemTables(id: string): Promise<TablesResponse> {
  return fetchJson<TablesResponse>(`${BASE}/problems/${encodeURIComponent(id)}/tables`)
}

export function completeProblem(
  id: string,
  mastery: number
): Promise<CompleteResponse> {
  return fetchJson<CompleteResponse>(
    `${BASE}/progress/${encodeURIComponent(id)}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'complete', mastery }),
    }
  )
}

export function updateProgress(
  id: string,
  data: { mastery_level?: number; notes?: string }
): Promise<ProgressUpdateResponse> {
  return fetchJson<ProgressUpdateResponse>(
    `${BASE}/progress/${encodeURIComponent(id)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }
  )
}

async function postSql<T>(path: string, body: { sql: string }): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let message = `API error ${res.status}`
    try {
      const data = await res.json()
      message = data?.detail?.message ?? data?.detail ?? message
    } catch {
      // 非 JSON 响应体，保留默认 message
    }
    const err = new Error(message) as Error & { status?: number }
    err.status = res.status
    throw err
  }
  return res.json()
}

export function executeSql(id: string, sql: string): Promise<SqlExecuteResult> {
  return postSql(`/problems/${encodeURIComponent(id)}/execute`, { sql })
}

export function submitSql(id: string, sql: string): Promise<SqlSubmitResult> {
  return postSql(`/problems/${encodeURIComponent(id)}/submit`, { sql })
}

export function getDraft(id: string): Promise<DraftResponse> {
  return fetchJson<DraftResponse>(`${BASE}/problems/${encodeURIComponent(id)}/draft`)
}

export function resetProgress(): Promise<{ reset: boolean; cleared: number }> {
  return fetchJson(`${BASE}/progress/reset`, { method: 'POST' })
}

export async function saveDraft(id: string, sql: string): Promise<void> {
  const res = await fetch(`${BASE}/problems/${encodeURIComponent(id)}/draft`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sql }),
  })
  if (!res.ok) throw new Error(`API error ${res.status}`)
}
