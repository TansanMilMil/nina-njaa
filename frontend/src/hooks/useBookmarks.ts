import { useState, useEffect } from 'react'

const KEY = 'ninanjaa_bookmarks'

function load(): number[] {
  try {
    const stored = JSON.parse(localStorage.getItem(KEY) || '[]')
    if (!Array.isArray(stored)) return []
    // migrate old format: [{id, name}] → [id]
    if (stored.length > 0 && typeof stored[0] === 'object' && stored[0] !== null) {
      return stored.map((b: { id: number }) => b.id).filter((id: unknown) => typeof id === 'number')
    }
    return stored.filter((id: unknown) => typeof id === 'number')
  } catch {
    return []
  }
}

export function useBookmarks() {
  const [bookmarks, setBookmarks] = useState<number[]>(load)

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(bookmarks))
  }, [bookmarks])

  const isBookmarked = (id: number) => bookmarks.includes(id)

  const toggle = (id: number) => {
    setBookmarks(prev =>
      prev.includes(id) ? prev.filter(b => b !== id) : [...prev, id]
    )
  }

  return { bookmarks, isBookmarked, toggle }
}
