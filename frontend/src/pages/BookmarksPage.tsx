import { useState, useEffect } from 'react'
import RecipeCard from '../components/RecipeCard'
import { useBookmarks } from '../hooks/useBookmarks'
import { getRecipesByIds } from '../api'
import type { Recipe } from '../api'

export default function BookmarksPage() {
  const { bookmarks } = useBookmarks()
  const [recipes, setRecipes] = useState<Recipe[]>([])

  useEffect(() => {
    if (bookmarks.length === 0) {
      setRecipes([])
      return
    }
    getRecipesByIds(bookmarks).then(setRecipes)
  }, [bookmarks])

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <h1 style={{ margin: 0, fontSize: '1.4rem' }}>ブックマーク</h1>
      {bookmarks.length === 0 ? (
        <p>ブックマークはまだありません</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {recipes.map(r => (
            <RecipeCard key={r.id} recipe={r} />
          ))}
        </div>
      )}
    </div>
  )
}
