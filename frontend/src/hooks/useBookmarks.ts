import { useState, useEffect } from 'react'

const KEY = 'ninanjaa_bookmarks'

interface BookmarkItem {
  id: number
  name: string
}

export function useBookmarks() {
  const [bookmarks, setBookmarks] = useState<BookmarkItem[]>(() => {
    try {
      return JSON.parse(localStorage.getItem(KEY) || '[]')
    } catch {
      return []
    }
  })

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(bookmarks))
  }, [bookmarks])

  const isBookmarked = (id: number) => bookmarks.some(b => b.id === id)

  const toggle = (item: BookmarkItem) => {
    setBookmarks(prev =>
      prev.some(b => b.id === item.id)
        ? prev.filter(b => b.id !== item.id)
        : [...prev, item]
    )
  }

  return { bookmarks, isBookmarked, toggle }
}
