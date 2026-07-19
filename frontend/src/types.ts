export interface ProgressInfo {
  status: string
  completed_count: number
  mastery_level: number
  last_practiced_at: string | null
}

export interface ProblemBrief {
  id: string
  category_id: string
  title: string
  difficulty: number
  tags: string[]
  progress: ProgressInfo | null
}

export interface CategoryInfo {
  id: string
  name: string
  db_file: string
  order: number
  stats: {
    total: number
    completed: number
    avg_mastery: number
  }
}

export interface CategoryListResponse {
  categories: CategoryInfo[]
  global_stats: {
    total: number
    completed: number
    avg_mastery: number
  }
}

export interface ProblemDetail {
  id: string
  category_id: string
  title: string
  difficulty: number
  tags: string[]
  description: string
  reference_sql: string
  tables: string[]
  hints: string[]
  progress: ProgressInfo | null
  db_file: string
  db_connection: string
}

export interface ColumnInfo {
  cid: number
  name: string
  type: string
  notnull: number
  dflt_value: string | null
  pk: number
}

export interface TableInfo {
  name: string
  columns: ColumnInfo[]
  row_count: number
  sample_rows: Record<string, unknown>[]
}

export interface TablesResponse {
  tables: TableInfo[]
  db_connection: string
}

export interface CompleteResponse {
  problem_id: string
  status: string
  completed_count: number
  mastery_level: number
  last_practiced_at: string
}

export interface ProgressUpdateResponse {
  problem_id: string
  mastery_level: number
  notes: string | null
}
