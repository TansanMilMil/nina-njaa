import { Link } from 'react-router-dom'
import { Star } from 'lucide-react'
import type { Recipe } from '../api'
import { cn } from '@/lib/utils'

interface RecipeCardProps {
  recipe: Recipe
  isBookmarked?: boolean
}

export default function RecipeCard({ recipe, isBookmarked }: RecipeCardProps) {
  return (
    <Link
      to={`/recipe/${recipe.id}`}
      className={cn(
        'block rounded-lg border bg-card px-3 py-2.5 text-card-foreground shadow-sm transition-colors hover:bg-accent',
        isBookmarked && 'border-primary bg-accent/40'
      )}
    >
      <div className="flex items-center gap-1.5">
        <span className="text-sm font-semibold">{recipe.name}</span>
        {isBookmarked && (
          <Star className="h-4 w-4 shrink-0 fill-primary text-primary" aria-label="ブックマーク済み" />
        )}
      </div>
      {recipe.ingredient_names && recipe.ingredient_names.length > 0 && (
        <div className="mt-0.5 truncate text-xs text-muted-foreground">
          {recipe.ingredient_names.join('・')}
        </div>
      )}
    </Link>
  )
}
