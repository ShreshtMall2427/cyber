import { useState } from 'react'
import type { Item } from '../types'

// Uncomment this import when you are ready to wire up the search logic:
// import { searchItems } from '../services/mockApi'

export interface UseSearchReturn {
  query: string
  setQuery: (q: string) => void
  results: Item[]
  isLoading: boolean
  error: string | null
}

export function useSearch(): UseSearchReturn {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Item[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // ── TODO: Implement debounced async search ──────────────────────────────
  //
  // 1. DEBOUNCE (300 ms)
  //    Wait 300 ms after the user stops typing before running the search.
  //    Cancel any pending timer when a new keystroke arrives.
  //    Return a cleanup function from useEffect to cancel on unmount.
  //
  // 2. ASYNC SEARCH
  //    Call searchItems(query) after the debounce delay fires.
  //    - Set isLoading = true before the call.
  //    - On success: update results, set isLoading = false.
  //    - On error:   store message in error, set isLoading = false.
  //    - Empty query: return all items (or clear results -- your choice).
  //
  // 3. STALE-RESPONSE PREVENTION
  //    Rapid typing causes overlapping in-flight requests.
  //    An older response MUST NOT replace a newer one.
  //    Example: user types "re" then quickly "react" -- if the "re" response
  //    arrives after "react", it must be discarded.
  //    Hint: a cancellation flag or an incrementing request-ID ref both work.
  //
  // 4. UNMOUNT CLEANUP
  //    No pending timers or state updates should run after the hook unmounts.
  //
  // You will need useEffect and useRef from React.
  // ───────────────────────────────────────────────────────────────────────

  return { query, setQuery, results, isLoading, error }
}
