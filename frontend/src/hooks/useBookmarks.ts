import { useState, useEffect, useContext } from 'react'
import { getRecipeBookmarks, addRecipeBookmark, removeRecipeBookmark } from '../api'
import { UserContext } from '../contexts/UserContext'

export function useBookmarks() {
  const currentUsername = useContext(UserContext)
  const [bookmarks, setBookmarks] = useState<number[]>([])

  useEffect(() => {
    if (currentUsername) {
      getRecipeBookmarks().then(setBookmarks).catch(() => {})
    } else {
      setBookmarks([])
    }
  }, [currentUsername])

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
