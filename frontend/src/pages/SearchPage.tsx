import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import SearchBar from '../components/SearchBar'
import RecipeCard from '../components/RecipeCard'
import { RecipeCardSkeleton } from '../components/Skeleton'
import { searchRecipes, getIngredientSuggestions, getRecipesByIds } from '../api'
import type { Recipe } from '../api'
import { useBookmarks } from '../hooks/useBookmarks'
import { useIngredientBookmarks } from '../hooks/useIngredientBookmarks'
import { Badge } from '@/components/ui/badge'

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const q = searchParams.get('q') ?? ''
  const [results, setResults] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const { bookmarks, isBookmarked } = useBookmarks()
  const { ingredientBookmarks } = useIngredientBookmarks()
  const [bookmarkRecipes, setBookmarkRecipes] = useState<Recipe[]>([])
  const [loadingBookmarks, setLoadingBookmarks] = useState(false)

  useEffect(() => {
    getIngredientSuggestions().then(setSuggestions).catch(() => {})
  }, [])

  useEffect(() => {
    if (bookmarks.length === 0) {
      setBookmarkRecipes([])
      return
    }
    setLoadingBookmarks(true)
    getRecipesByIds(bookmarks).then(data => {
      setBookmarkRecipes(data)
      setLoadingBookmarks(false)
    })
  }, [bookmarks])

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
    <div className="flex h-full flex-col gap-4 overflow-hidden">
      <div className="flex flex-shrink-0 flex-col gap-2">
        <SearchBar value={q} onChange={handleChange} />
        {suggestions.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {suggestions.map(s => (
              <Badge
                key={s}
                variant={q === s ? 'default' : 'secondary'}
                onClick={() => handleChange(s)}
                className="cursor-pointer rounded-full"
              >
                {s}
              </Badge>
            ))}
          </div>
        )}
      </div>
      {showBookmarks ? (
        <div className="flex flex-1 flex-col gap-4 overflow-hidden">
          {ingredientBookmarks.length > 0 && (
            <div className="flex-shrink-0">
              <h2 className="mb-2 text-lg font-semibold">ブックマーク済み食材</h2>
              <div className="flex flex-wrap gap-1.5">
                {ingredientBookmarks.map(name => (
                  <Badge
                    key={name}
                    variant="outline"
                    onClick={() => handleChange(name)}
                    className="cursor-pointer gap-1 rounded-full border-primary bg-accent/40"
                  >
                    <span className="text-primary">★</span> {name}
                  </Badge>
                ))}
              </div>
            </div>
          )}
          <div className="flex flex-1 flex-col overflow-hidden">
            <h2 className="mb-3 flex-shrink-0 text-lg font-semibold">ブックマーク済みレシピ</h2>
            {bookmarks.length === 0 ? (
              <p className="text-sm text-muted-foreground">レシピのブックマークはまだありません</p>
            ) : (
              <div className="flex flex-1 flex-col gap-3 overflow-y-auto">
                {loadingBookmarks
                  ? Array.from({ length: bookmarks.length }, (_, i) => <RecipeCardSkeleton key={i} />)
                  : bookmarkRecipes.map(r => <RecipeCard key={r.id} recipe={r} isBookmarked />)
                }
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="flex flex-1 flex-col overflow-hidden">
          {!loading && (
            <p className="mb-3 flex-shrink-0 text-sm text-muted-foreground">
              {results.length === 0 ? '該当するレシピが見つかりませんでした' : `${results.length}件のレシピが見つかりました`}
            </p>
          )}
          <div className="flex flex-1 flex-col gap-3 overflow-y-auto">
            {loading
              ? Array.from({ length: 4 }, (_, i) => <RecipeCardSkeleton key={i} />)
              : results.map(recipe => <RecipeCard key={recipe.id} recipe={recipe} isBookmarked={isBookmarked(recipe.id)} />)
            }
          </div>
        </div>
      )}
    </div>
  )
}
