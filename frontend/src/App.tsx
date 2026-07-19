import { Routes, Route, Link } from 'react-router-dom'
import CategoryListPage from './pages/CategoryListPage'
import ProblemListPage from './pages/ProblemListPage'

function App() {
  return (
    <div className="min-h-screen bg-gray-100">
      {/* Dark Header */}
      <header className="bg-gray-900 text-white shadow-md">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="text-xl font-bold tracking-tight hover:text-green-400 transition-colors">
            SQL Practice Platform
          </Link>
          <nav className="flex gap-6 text-sm text-gray-300">
            <Link to="/" className="hover:text-white transition-colors">Categories</Link>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Routes>
          <Route path="/" element={<CategoryListPage />} />
          <Route path="/category/:id" element={<ProblemListPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
