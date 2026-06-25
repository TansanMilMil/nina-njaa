import { useState, useEffect } from 'react'
import { getRecipeBookmarks, addRecipeBookmark, removeRecipeBookmark } from '../api'

export function useBookmarks() {
  const [bookmarks, setBookmarks] = useState<number[]>([])

  useEffect(() => {
    getRecipeBookmarks().then(setBookmarks).catch(() => {})
  }, [])

  const isBookmarked = (id: number) => bookmarks.includes(id)

  const toggle = async (id: number) => {
    const wasBookmarked = bookmarks.includes(id)
    setBookmarks(prev => wasBookmarked ? prev.filter(b => b !== id) : [...prev, id])
    try {
      if (wasBookmarked) {
        await removeRecipeBookmark(id)
      } else {
        await addRecipeBookmark(id)
      }
    } catch {
      setBookmarks(prev => wasBookmarked ? [...prev, id] : prev.filter(b => b !== id))
    }
  }

  return { bookmarks, isBookmarked, toggle }
}
