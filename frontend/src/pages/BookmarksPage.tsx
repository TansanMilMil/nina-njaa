import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import RecipeCard from '../components/RecipeCard'
import { useBookmarks } from '../hooks/useBookmarks'
import { useIngredientBookmarks } from '../hooks/useIngredientBookmarks'
import { getRecipesByIds } from '../api'
import type { Recipe } from '../api'

type Tab = 'recipes' | 'ingredients'

export default function BookmarksPage() {
  const { bookmarks } = useBookmarks()
  const { ingredientBookmarks, toggleIngredient } = useIngredientBookmarks()
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [tab, setTab] = useState<Tab>('recipes')

  useEffect(() => {
    if (bookmarks.length === 0) {
      setRecipes([])
      return
    }
    getRecipesByIds(bookmarks).then(setRecipes)
  }, [bookmarks])

  const tabStyle = (active: boolean): React.CSSProperties => ({
    flex: 1,
    padding: '0.6rem 0',
    fontSize: '0.95rem',
    fontWeight: active ? 600 : 400,
    background: 'none',
    border: 'none',
    borderBottom: active ? '2px solid #f0a500' : '2px solid transparent',
    color: active ? '#f0a500' : '#888',
    cursor: 'pointer',
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <h1 style={{ margin: 0, fontSize: '1.4rem' }}>ブックマーク</h1>

      <div style={{ display: 'flex', borderBottom: '1px solid #eee' }}>
        <button style={tabStyle(tab === 'recipes')} onClick={() => setTab('recipes')}>
          レシピ {bookmarks.length > 0 && <span style={{ fontSize: '0.8rem' }}>({bookmarks.length})</span>}
        </button>
        <button style={tabStyle(tab === 'ingredients')} onClick={() => setTab('ingredients')}>
          食材 {ingredientBookmarks.length > 0 && <span style={{ fontSize: '0.8rem' }}>({ingredientBookmarks.length})</span>}
        </button>
      </div>

      {tab === 'recipes' && (
        bookmarks.length === 0 ? (
          <p style={{ margin: 0, color: '#888', fontSize: '0.9rem' }}>レシピのブックマークはまだありません</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {recipes.map(r => (
              <RecipeCard key={r.id} recipe={r} isBookmarked />
            ))}
          </div>
        )
      )}

      {tab === 'ingredients' && (
        ingredientBookmarks.length === 0 ? (
          <p style={{ margin: 0, color: '#888', fontSize: '0.9rem' }}>食材のブックマークはまだありません</p>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {ingredientBookmarks.map(name => (
              <div
                key={name}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.3rem',
                  padding: '0.3rem 0.6rem 0.3rem 0.75rem',
                  border: '1px solid #f0a500',
                  borderRadius: '999px',
                  background: '#fffbf0',
                  fontSize: '0.85rem',
                }}
              >
                <Link
                  to={`/?q=${encodeURIComponent(name)}`}
                  style={{ color: '#333', textDecoration: 'none' }}
                >
                  {name}
                </Link>
                <button
                  type="button"
                  onClick={() => toggleIngredient(name)}
                  title="ブックマーク解除"
                  style={{
                    background: 'none',
                    border: 'none',
                    padding: 0,
                    cursor: 'pointer',
                    fontSize: '0.75rem',
                    color: '#aaa',
                    lineHeight: 1,
                  }}
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
