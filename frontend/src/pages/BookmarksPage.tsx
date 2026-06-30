import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { X } from 'lucide-react'
import RecipeCard from '../components/RecipeCard'
import { RecipeCardSkeleton } from '../components/Skeleton'
import { useBookmarks } from '../hooks/useBookmarks'
import { useIngredientBookmarks } from '../hooks/useIngredientBookmarks'
import { getRecipesByIds, getCookedLogs } from '../api'
import type { Recipe } from '../api'
import { cn } from '@/lib/utils'

type Tab = 'recipes' | 'ingredients'

export default function BookmarksPage() {
  const { bookmarks, toggle } = useBookmarks()
  const { ingredientBookmarks, toggleIngredient } = useIngredientBookmarks()
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loadingRecipes, setLoadingRecipes] = useState(false)
  const [cookedCountMap, setCookedCountMap] = useState<Map<number, number>>(new Map())
  const [tab, setTab] = useState<Tab>('recipes')

  useEffect(() => {
    if (bookmarks.length === 0) {
      setRecipes([])
      return
    }
    setLoadingRecipes(true)
    getRecipesByIds(bookmarks).then(data => {
      setRecipes(data)
      setLoadingRecipes(false)
    })
  }, [bookmarks])

  useEffect(() => {
    getCookedLogs().then(logs => {
      setCookedCountMap(new Map(logs.map(l => [l.recipe_id, l.count])))
    }).catch(() => {})
  }, [])

  const tabClass = (active: boolean) =>
    cn(
      'flex-1 border-b-2 py-2.5 text-sm transition-colors',
      active
        ? 'border-primary font-semibold text-primary'
        : 'border-transparent text-muted-foreground hover:text-foreground'
    )

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">ブックマーク</h1>

      <div className="flex border-b">
        <button className={tabClass(tab === 'recipes')} onClick={() => setTab('recipes')}>
          レシピ {bookmarks.length > 0 && <span className="text-xs">({bookmarks.length})</span>}
        </button>
        <button className={tabClass(tab === 'ingredients')} onClick={() => setTab('ingredients')}>
          食材 {ingredientBookmarks.length > 0 && <span className="text-xs">({ingredientBookmarks.length})</span>}
        </button>
      </div>

      {tab === 'recipes' && (
        bookmarks.length === 0 ? (
          <p className="text-sm text-muted-foreground">レシピのブックマークはまだありません</p>
        ) : (
          <div className="flex flex-col gap-3">
            {loadingRecipes
              ? Array.from({ length: bookmarks.length }, (_, i) => <RecipeCardSkeleton key={i} />)
              : recipes.map(r => <RecipeCard key={r.id} recipe={r} isBookmarked onBookmarkToggle={() => toggle(r.id)} cookedCount={cookedCountMap.get(r.id) ?? 0} />)
            }
          </div>
        )
      )}

      {tab === 'ingredients' && (
        ingredientBookmarks.length === 0 ? (
          <p className="text-sm text-muted-foreground">食材のブックマークはまだありません</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {ingredientBookmarks.map(name => (
              <div
                key={name}
                className="flex items-center gap-1 rounded-full border border-primary bg-accent/40 py-1 pl-3 pr-1 text-sm"
              >
                <Link to={`/?q=${encodeURIComponent(name)}`} className="text-foreground">
                  {name}
                </Link>
                <button
                  type="button"
                  onClick={() => toggleIngredient(name)}
                  title="ブックマーク解除"
                  className="rounded-full p-0.5 text-muted-foreground hover:text-foreground"
                >
                  <X className="h-3.5 w-3.5" />
                </button>
              </div>
            ))}
          </div>
        )
      )}
    </div>
  )
}
