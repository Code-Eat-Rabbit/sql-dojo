import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCategories } from '../api'
import type { CategoryInfo, CategoryListResponse } from '../types'

function GlobalProgressBar({ total, completed }: { total: number; completed: number }) {
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0
  return (
    <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-lg font-semibold text-gray-800">Overall Progress</h2>
        <span className="text-sm text-gray-500">
          {completed} / {total} completed ({pct}%)
        </span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div
          className="bg-green-500 h-3 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function StarRating({ rating }: { rating: number }) {
  return (
    <div className="flex gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <svg
          key={star}
          className={`w-4 h-4 ${star <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
      ))}
    </div>
  )
}

function CategoryCard({ category }: { category: CategoryInfo }) {
  const navigate = useNavigate()
  const { stats } = category
  const pct = stats.total > 0 ? (stats.completed / stats.total) * 100 : 0

  return (
    <div
      onClick={() => navigate(`/category/${category.id}`)}
      className="bg-white rounded-lg shadow-sm p-5 cursor-pointer hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 border border-gray-100"
    >
      <h3 className="text-lg font-semibold text-gray-800 mb-3">{category.name}</h3>

      {/* Progress bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-500 mb-1">
          <span>{stats.completed} / {stats.total} problems</span>
          <span>{Math.round(pct)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      {/* Average mastery stars */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <span>Avg mastery:</span>
        <StarRating rating={Math.round(stats.avg_mastery)} />
        <span className="text-xs">({stats.avg_mastery.toFixed(1)})</span>
      </div>
    </div>
  )
}

export default function CategoryListPage() {
  const [data, setData] = useState<CategoryListResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getCategories()
      .then(setData)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-gray-900" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
        Failed to load categories: {error}
      </div>
    )
  }

  if (!data) return null

  return (
    <div>
      <GlobalProgressBar
        total={data.global_stats.total}
        completed={data.global_stats.completed}
      />

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.categories.map((cat) => (
          <CategoryCard key={cat.id} category={cat} />
        ))}
      </div>

      {data.categories.length === 0 && (
        <div className="text-center py-12 text-gray-400">
          No categories available yet.
        </div>
      )}
    </div>
  )
}
