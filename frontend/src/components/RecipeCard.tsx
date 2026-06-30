import { Link } from 'react-router-dom'
import { Star } from 'lucide-react'
import type { Recipe } from '../api'
import { cn } from '@/lib/utils'

interface RecipeCardProps {
  recipe: Recipe
  isBookmarked?: boolean
  onBookmarkToggle?: () => void
  cookedCount?: number
}

export default function RecipeCard({ recipe, isBookmarked, onBookmarkToggle, cookedCount }: RecipeCardProps) {
  return (
    <Link
      to={`/recipe/${recipe.id}`}
      target="_blank"
      rel="noopener noreferrer"
      className={cn(
        'block rounded-lg border bg-card text-card-foreground shadow-sm transition-colors hover:bg-accent',
        isBookmarked && 'border-primary bg-accent/40'
      )}
    >
      <div className="flex gap-3">
        {recipe.image_path && (
          <img
            src={`/uploads/${recipe.image_path}`}
            alt={recipe.name ?? ''}
            className="h-20 w-20 shrink-0 rounded-l-lg object-cover"
          />
        )}
        <div className={cn('min-w-0 flex-1 py-2.5', recipe.image_path ? 'pr-3' : 'px-3')}>
          <div className="flex items-center gap-1.5">
            <span className="text-sm font-semibold">{recipe.name}</span>
            {isBookmarked && onBookmarkToggle ? (
              <button
                type="button"
                onClick={e => { e.preventDefault(); e.stopPropagation(); onBookmarkToggle() }}
                title="ブックマーク解除"
                className="shrink-0 text-primary hover:text-muted-foreground"
              >
                <Star className="h-4 w-4 fill-primary" />
              </button>
            ) : isBookmarked ? (
              <Star className="h-4 w-4 shrink-0 fill-primary text-primary" aria-label="ブックマーク済み" />
            ) : null}
          </div>
          {recipe.ingredient_names && recipe.ingredient_names.length > 0 && (
            <div className="mt-0.5 truncate text-xs text-muted-foreground">
              {recipe.ingredient_names.join('・')}
            </div>
          )}
          {cookedCount !== undefined && cookedCount > 0 && (
            <div className="mt-1 text-xs font-medium text-primary">
              {cookedCount}回作った
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}
