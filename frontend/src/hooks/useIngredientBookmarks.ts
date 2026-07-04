import { useState, useEffect, useContext } from 'react'
import { getIngredientBookmarks, addIngredientBookmark, removeIngredientBookmark } from '../api'
import { UserContext } from '../contexts/UserContext'

export function useIngredientBookmarks() {
  const currentUsername = useContext(UserContext)
  const [bookmarks, setBookmarks] = useState<string[]>([])

  useEffect(() => {
    if (currentUsername) {
      getIngredientBookmarks().then(setBookmarks).catch(() => {})
    } else {
      setBookmarks([])
    }
  }, [currentUsername])

  const isIngredientBookmarked = (name: string) => bookmarks.includes(name)

  const toggleIngredient = async (name: string) => {
    const wasBookmarked = bookmarks.includes(name)
    setBookmarks(prev => wasBookmarked ? prev.filter(b => b !== name) : [...prev, name])
    try {
      if (wasBookmarked) {
        await removeIngredientBookmark(name)
      } else {
        await addIngredientBookmark(name)
      }
    } catch {
      setBookmarks(prev => wasBookmarked ? [...prev, name] : prev.filter(b => b !== name))
    }
  }

  return { ingredientBookmarks: bookmarks, isIngredientBookmarked, toggleIngredient }
}
