import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import RecipeCard from '../components/RecipeCard'
import { searchRecipes } from '../api'
import type { Recipe } from '../api'
import { useBookmarks } from '../hooks/useBookmarks'

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const q = searchParams.get('q') ?? ''
  const [results, setResults] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(false)
  const { bookmarks } = useBookmarks()

  const handleChange = (value: string) => {
    if (value) {
      setSearchParams({ q: value })
    } else {
      setSearchParams({})
    }
  }

  useEffect(() => {
    if (!q) {
      setResults([])
      return
    }
    let cancelled = false
    setLoading(true)
    searchRecipes(q).then(data => {
      if (!cancelled) {
        setResults(data)
        setLoading(false)
      }
    })
    return () => {
      cancelled = true
    }
  }, [q])

  const showBookmarks = q === ''

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', height: '100%', overflow: 'hidden' }}>
      <SearchBar value={q} onChange={handleChange} />
      {showBookmarks ? (
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
          <h2 style={{ margin: '0 0 0.75rem', fontSize: '1.1rem', flexShrink: 0 }}>ブックマーク済みレシピ</h2>
          {bookmarks.length === 0 ? (
            <p>ブックマークはまだありません</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', flex: 1 }}>
              {bookmarks.map(b => (
                <RecipeCard
                  key={b.id}
                  recipe={{
                    id: b.id,
                    name: b.name,
                    source_url: '',
                    servings: null,
                    scraped_at: null
                  }}
                />
              ))}
            </div>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, overflow: 'hidden' }}>
          {!loading && (
            <p style={{ margin: '0 0 0.75rem', fontSize: '0.9rem', color: '#666', flexShrink: 0 }}>
              {results.length === 0 ? '該当するレシピが見つかりませんでした' : `${results.length}件のレシピが見つかりました`}
            </p>
          )}
          {loading && (
            <p style={{ margin: '0 0 0.75rem', fontSize: '0.9rem', color: '#666', flexShrink: 0 }}>検索中...</p>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', overflowY: 'auto', flex: 1 }}>
            {results.map(recipe => <RecipeCard key={recipe.id} recipe={recipe} />)}
          </div>
        </div>
      )}
    </div>
  )
}
