import type {
  CategoryListResponse,
  ProblemBrief,
  ProblemDetail,
  TablesResponse,
  CompleteResponse,
  ProgressUpdateResponse,
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
  category: { id: string; name: string; db_file: string; order: number } | null
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
