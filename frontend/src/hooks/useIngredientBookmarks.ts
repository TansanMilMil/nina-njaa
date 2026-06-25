import { useState, useEffect } from 'react'

const KEY = 'ninanjaa_ingredient_bookmarks'

function load(): string[] {
  try {
    const stored = JSON.parse(localStorage.getItem(KEY) || '[]')
    if (!Array.isArray(stored)) return []
    return stored.filter((s: unknown) => typeof s === 'string')
  } catch {
    return []
  }
}

export function useIngredientBookmarks() {
  const [bookmarks, setBookmarks] = useState<string[]>(load)

  useEffect(() => {
    localStorage.setItem(KEY, JSON.stringify(bookmarks))
  }, [bookmarks])

  const isIngredientBookmarked = (name: string) => bookmarks.includes(name)

  const toggleIngredient = (name: string) => {
    setBookmarks(prev =>
      prev.includes(name) ? prev.filter(b => b !== name) : [...prev, name]
    )
  }

  return { ingredientBookmarks: bookmarks, isIngredientBookmarked, toggleIngredient }
}
