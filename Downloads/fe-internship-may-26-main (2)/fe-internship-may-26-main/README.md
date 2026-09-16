# Frontend Tools Search

A minimal React app for searching a curated list of frontend frameworks, libraries, and tools.

---

## Setup

```bash
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

---

## About

The app already has a working layout, search input, item cards, loading skeleton, and empty state.

**Your job is to implement the missing logic.** The places to fill in are marked with TODO comments.

---

## Task -- Implement `useSearch` (`src/hooks/useSearch.ts`)

The hook already declares all the state you need. You must wire up the logic:

### 1. Debounced search

- Wait **300 ms** after the user stops typing before running a search
- Cancel any pending timer when a new keystroke arrives
- Return a cleanup function from your `useEffect` to cancel on unmount

### 2. Async search

- Call `searchItems(query)` from `src/services/mockApi.ts`
- Show a loading state while the request is in flight
- Handle errors gracefully
- When the query is empty, show all items

### 3. Stale-response prevention

- Rapid typing can cause multiple overlapping requests
- An older response must never replace a newer one
- Example: typing "re" then quickly "react" -- the "re" response must be discarded if it arrives after "react"

### 4. Cleanup on unmount

- No pending timers or state updates should run after the component unmounts

### 5. App.tsx wiring (small)

Replace the placeholder `<div>` in `App.tsx` with conditional rendering:
- `<LoadingState />` when loading
- `<ItemList />` when results exist
- `<EmptyState />` when empty

---

## Bonus

Optional -- attempt if you finish early:

- Highlight matching text in results
- Reusable `useDebounce` custom hook
- Keyboard shortcut already wired (`/` focuses the input) -- add more if you like
- Persist query in URL (`?q=react`)

---

## Focus

Focus on correctness first. A clean working hook beats a half-finished bonus attempt.

---

## Project Structure

```
src/
  components/
    SearchInput.tsx    <- complete
    ItemCard.tsx       <- complete
    ItemList.tsx       <- complete
    LoadingState.tsx   <- complete
    EmptyState.tsx     <- complete
  hooks/
    useSearch.ts       <- YOUR TASK
  services/
    mockApi.ts         <- complete (mock, variable delay)
  types/
    index.ts           <- type definitions
  App.tsx              <- one small TODO (conditional rendering)
```

---

## Evaluation

| Area | What we look for |
|---|---|
| Debounce | Correct timer cleanup, no leaks |
| Async handling | Loading state, error handling |
| Stale prevention | Old responses never win over newer ones |
| Cleanup | No updates after unmount |
| Code quality | Readable, no unnecessary abstractions |
