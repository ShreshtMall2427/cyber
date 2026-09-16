import { SearchInput } from './components/SearchInput'
import { ItemList } from './components/ItemList'
import { LoadingState } from './components/LoadingState'
import { EmptyState } from './components/EmptyState'
import { useSearch } from './hooks/useSearch'

export default function App() {
  const { query, setQuery, results, isLoading, error } = useSearch()

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <div className="max-w-2xl mx-auto px-4 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-1">Frontend Tools</h1>
          <p className="text-gray-400 text-sm">Search across popular frameworks, libraries and tooling</p>
        </div>

        <div className="mb-6">
          <SearchInput
            value={query}
            onChange={setQuery}
            placeholder="Search by name, category, or description..."
          />
          <p className="mt-2 text-xs text-gray-600">
            Press{' '}
            <kbd className="px-1 py-0.5 bg-gray-800 rounded text-gray-400 font-mono text-xs">/</kbd>
            {' '}to focus
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-sm">
            {error}
          </div>
        )}

        {/* TODO: Replace this placeholder with conditional rendering.
            - Show <LoadingState /> when isLoading is true
            - Show <ItemList items={results} /> when results exist and not loading
            - Show <EmptyState query={query} /> when results are empty and not loading */}
        <div className="text-gray-500 text-sm text-center py-16">
          Implement useSearch to see results here.
        </div>
      </div>
    </div>
  )
}
