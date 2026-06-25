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
import { Button } from '@/components/ui/button'
import { ChevronUp } from 'lucide-react'

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
  const [showScrollTop, setShowScrollTop] = useState(false)

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

  useEffect(() => {
    const container = document.querySelector('main')
    if (!container) return
    const handleScroll = () => setShowScrollTop(container.scrollTop > 200)
    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => container.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToTop = () => document.querySelector('main')?.scrollTo({ top: 0, behavior: 'smooth' })

  const showBookmarks = q === ''

  return (
    <>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
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
          <div className="flex flex-col gap-4">
            {ingredientBookmarks.length > 0 && (
              <div>
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
            <div className="flex flex-col">
              <h2 className="mb-3 text-lg font-semibold">ブックマーク済みレシピ</h2>
              {bookmarks.length === 0 ? (
                <p className="text-sm text-muted-foreground">レシピのブックマークはまだありません</p>
              ) : (
                <div className="flex flex-col gap-3">
                  {loadingBookmarks
                    ? Array.from({ length: bookmarks.length }, (_, i) => <RecipeCardSkeleton key={i} />)
                    : bookmarkRecipes.map(r => <RecipeCard key={r.id} recipe={r} isBookmarked />)
                  }
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col">
            {!loading && (
              <p className="mb-3 text-sm text-muted-foreground">
                {results.length === 0 ? '該当するレシピが見つかりませんでした' : `${results.length}件のレシピが見つかりました`}
              </p>
            )}
            <div className="flex flex-col gap-3">
              {loading
                ? Array.from({ length: 4 }, (_, i) => <RecipeCardSkeleton key={i} />)
                : results.map(recipe => <RecipeCard key={recipe.id} recipe={recipe} isBookmarked={isBookmarked(recipe.id)} />)
              }
            </div>
          </div>
        )}
      </div>
      {showScrollTop && (
        <Button
          size="icon"
          onClick={scrollToTop}
          className="fixed bottom-6 right-6 z-50 rounded-full shadow-lg"
          aria-label="トップへ戻る"
        >
          <ChevronUp className="h-5 w-5" />
        </Button>
      )}
    </>
  )
}
