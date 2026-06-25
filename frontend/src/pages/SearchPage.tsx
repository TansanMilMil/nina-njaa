import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import RecipeCard from '../components/RecipeCard'
import ImportFromUrl from '../components/ImportFromUrl'
import { searchRecipes } from '../api'
import type { Recipe } from '../api'
import { useBookmarks } from '../hooks/useBookmarks'

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const q = searchParams.get('q') ?? ''
  const [results, setResults] = useState<Recipe[]>([])
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
    searchRecipes(q).then(data => {
      if (!cancelled) setResults(data)
    })
    return () => {
      cancelled = true
    }
  }, [q])

  const showBookmarks = q === ''

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <ImportFromUrl />
      <SearchBar value={q} onChange={handleChange} />
      {showBookmarks ? (
        <>
          <h2 style={{ margin: 0, fontSize: '1.1rem' }}>ブックマーク済みレシピ</h2>
          {bookmarks.length === 0 ? (
            <p>ブックマークはまだありません</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
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
        </>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {results.length === 0 ? (
            <p>該当するレシピが見つかりませんでした</p>
          ) : (
            results.map(recipe => <RecipeCard key={recipe.id} recipe={recipe} />)
          )}
        </div>
      )}
    </div>
  )
}
