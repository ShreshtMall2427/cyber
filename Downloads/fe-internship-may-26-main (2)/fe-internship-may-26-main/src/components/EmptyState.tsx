export function EmptyState({ query }: { query: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-4xl mb-4">🔍</div>
      {query.trim() ? (
        <>
          <p className="text-gray-300 font-medium mb-1">No results for &ldquo;{query.trim()}&rdquo;</p>
          <p className="text-gray-500 text-sm">Try a different search term</p>
        </>
      ) : (
        <>
          <p className="text-gray-300 font-medium mb-1">Start typing to search</p>
          <p className="text-gray-500 text-sm">Find frameworks, libraries and tools</p>
        </>
      )}
    </div>
  )
}
