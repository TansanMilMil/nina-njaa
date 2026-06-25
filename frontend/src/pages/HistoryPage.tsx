import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import RecipeCard from '../components/RecipeCard'
import { RecipeCardSkeleton } from '../components/Skeleton'
import { useBookmarks } from '../hooks/useBookmarks'
import { getRecentViewedRecipes, getRecentViewedIngredients } from '../api'
import type { Recipe } from '../api'
import { cn } from '@/lib/utils'

type Tab = 'recipes' | 'ingredients'

export default function HistoryPage() {
  const { bookmarks } = useBookmarks()
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [ingredients, setIngredients] = useState<string[]>([])
  const [loadingRecipes, setLoadingRecipes] = useState(true)
  const [loadingIngredients, setLoadingIngredients] = useState(true)
  const [tab, setTab] = useState<Tab>('recipes')

  useEffect(() => {
    getRecentViewedRecipes().then(data => {
      setRecipes(data)
      setLoadingRecipes(false)
    })
    getRecentViewedIngredients().then(data => {
      setIngredients(data)
      setLoadingIngredients(false)
    })
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
      <h1 className="text-2xl font-bold">最近見たもの</h1>

      <div className="flex border-b">
        <button className={tabClass(tab === 'recipes')} onClick={() => setTab('recipes')}>
          レシピ {recipes.length > 0 && <span className="text-xs">({recipes.length})</span>}
        </button>
        <button className={tabClass(tab === 'ingredients')} onClick={() => setTab('ingredients')}>
          食材 {ingredients.length > 0 && <span className="text-xs">({ingredients.length})</span>}
        </button>
      </div>

      {tab === 'recipes' && (
        loadingRecipes ? (
          <div className="flex flex-col gap-3">
            {Array.from({ length: 3 }, (_, i) => <RecipeCardSkeleton key={i} />)}
          </div>
        ) : recipes.length === 0 ? (
          <p className="text-sm text-muted-foreground">まだレシピを見ていません</p>
        ) : (
          <div className="flex flex-col gap-3">
            {recipes.map(r => (
              <RecipeCard key={r.id} recipe={r} isBookmarked={bookmarks.includes(r.id)} />
            ))}
          </div>
        )
      )}

      {tab === 'ingredients' && (
        loadingIngredients ? (
          <div className="flex flex-wrap gap-2">
            {Array.from({ length: 8 }, (_, i) => (
              <div key={i} className="h-8 w-16 animate-pulse rounded-full bg-muted" />
            ))}
          </div>
        ) : ingredients.length === 0 ? (
          <p className="text-sm text-muted-foreground">まだ食材を見ていません</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {ingredients.map(name => (
              <Link
                key={name}
                to={`/?q=${encodeURIComponent(name)}`}
                className="rounded-full border border-border bg-accent/40 px-3 py-1 text-sm text-foreground hover:bg-accent"
              >
                {name}
              </Link>
            ))}
          </div>
        )
      )}
    </div>
  )
}
