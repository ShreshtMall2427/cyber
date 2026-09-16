export function LoadingState() {
  return (
    <div className="flex flex-col gap-3" aria-busy="true" aria-label="Loading results">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="bg-gray-800 rounded-xl p-4 border border-gray-700 animate-pulse">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-2">
                <div className="h-4 w-24 bg-gray-700 rounded" />
                <div className="h-4 w-16 bg-gray-700 rounded-full" />
              </div>
              <div className="h-3 w-full bg-gray-700 rounded mb-1.5" />
              <div className="h-3 w-3/4 bg-gray-700 rounded" />
            </div>
            <div className="h-4 w-8 bg-gray-700 rounded flex-shrink-0" />
          </div>
        </div>
      ))}
    </div>
  )
}
