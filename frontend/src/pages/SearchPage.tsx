import { useState, useEffect, useContext, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { UserContext } from '../contexts/UserContext'
import SearchBar from '../components/SearchBar'
import RecipeCard from '../components/RecipeCard'
import { RecipeCardSkeleton } from '../components/Skeleton'
import { searchRecipes, getIngredientSuggestions, getRecentViewedRecipes, getCookedLogs, getCategories } from '../api'
import type { Recipe, Category } from '../api'
import { useBookmarks } from '../hooks/useBookmarks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ChevronUp } from 'lucide-react'

function parseCategoryIds(value: string | null): number[] {
  if (!value) return []
  return value.split(',').map(Number).filter(n => Number.isInteger(n) && n > 0)
}

export default function SearchPage() {
  const currentUsername = useContext(UserContext)
  const [searchParams, setSearchParams] = useSearchParams()
  const q = searchParams.get('q') ?? ''
  const categoryParam = searchParams.get('category')
  const selectedCategoryIds = useMemo(() => parseCategoryIds(categoryParam), [categoryParam])
  const [results, setResults] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])
  const { isBookmarked } = useBookmarks()
  const [recentRecipes, setRecentRecipes] = useState<Recipe[]>([])
  const [loadingRecent, setLoadingRecent] = useState(false)
  const [cookedCountMap, setCookedCountMap] = useState<Map<number, number>>(new Map())
  const [showScrollTop, setShowScrollTop] = useState(false)
  const [categories, setCategories] = useState<Category[]>([])

  useEffect(() => {
    getCategories().then(setCategories).catch(() => {})
  }, [])

  useEffect(() => {
    if (currentUsername) {
      getIngredientSuggestions().then(setSuggestions).catch(() => {})
    } else {
      setSuggestions([])
    }
  }, [currentUsername])

  useEffect(() => {
    if (currentUsername) {
      setLoadingRecent(true)
      Promise.all([getRecentViewedRecipes(), getCookedLogs()]).then(([recipes, logs]) => {
        setRecentRecipes(recipes)
        setCookedCountMap(new Map(logs.map(l => [l.recipe_id, l.count])))
        setLoadingRecent(false)
      }).catch(() => setLoadingRecent(false))
    } else {
      setRecentRecipes([])
      setCookedCountMap(new Map())
    }
  }, [currentUsername])

  const updateSearchParams = (nextQ: string, nextCategoryIds: number[]) => {
    const params: Record<string, string> = {}
    if (nextQ) params.q = nextQ
    if (nextCategoryIds.length > 0) params.category = nextCategoryIds.join(',')
    setSearchParams(params)
  }

  const handleChange = (value: string) => {
    updateSearchParams(value, selectedCategoryIds)
  }

  const toggleCategory = (id: number) => {
    const next = selectedCategoryIds.includes(id)
      ? selectedCategoryIds.filter(c => c !== id)
      : [...selectedCategoryIds, id]
    updateSearchParams(q, next)
  }

  useEffect(() => {
    if (!q && selectedCategoryIds.length === 0) {
      setResults([])
      return
    }
    let cancelled = false
    setLoading(true)
    searchRecipes(q, selectedCategoryIds).then(data => {
      if (!cancelled) {
        setResults(data)
        setLoading(false)
      }
    })
    return () => {
      cancelled = true
    }
  }, [q, selectedCategoryIds])

  useEffect(() => {
    const container = document.querySelector('main')
    if (!container) return
    const handleScroll = () => setShowScrollTop(container.scrollTop > 200)
    container.addEventListener('scroll', handleScroll, { passive: true })
    return () => container.removeEventListener('scroll', handleScroll)
  }, [])

  const scrollToTop = () => document.querySelector('main')?.scrollTo({ top: 0, behavior: 'smooth' })

  const showRecent = q === '' && selectedCategoryIds.length === 0

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
          {categories.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {categories.map(c => (
                <Badge
                  key={c.id}
                  variant={selectedCategoryIds.includes(c.id) ? 'default' : 'secondary'}
                  onClick={() => toggleCategory(c.id)}
                  className="cursor-pointer rounded-full"
                >
                  {c.name}
                </Badge>
              ))}
            </div>
          )}
        </div>
        {showRecent ? (
          <div className="flex flex-col">
            <h2 className="mb-3 text-lg font-semibold">最近みたレシピ</h2>
            {loadingRecent ? (
              <div className="flex flex-col gap-3">
                {Array.from({ length: 3 }, (_, i) => <RecipeCardSkeleton key={i} />)}
              </div>
            ) : recentRecipes.length === 0 ? (
              <p className="text-sm text-muted-foreground">まだレシピを閲覧していません</p>
            ) : (
              <div className="flex flex-col gap-3">
                {recentRecipes.map(r => <RecipeCard key={r.id} recipe={r} isBookmarked={isBookmarked(r.id)} cookedCount={cookedCountMap.get(r.id) ?? 0} />)}
              </div>
            )}
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
                : results.map(recipe => <RecipeCard key={recipe.id} recipe={recipe} isBookmarked={isBookmarked(recipe.id)} cookedCount={cookedCountMap.get(recipe.id) ?? 0} />)
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
