import { Link } from 'react-router-dom'
import { Star } from 'lucide-react'
import type { Ingredient } from '../api'
import { groupIngredients, scaleQuantity } from '../lib/ingredients'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

const MULTIPLIER_PRESETS = [0.5, 1, 2, 3]

interface RecipeIngredientsSectionProps {
  ingredients: Ingredient[]
  multiplier: number
  multiplierInput: string
  isIngredientBookmarked: (name: string) => boolean
  onToggleIngredient: (name: string) => void
  onMultiplierInputChange: (value: string) => void
  onMultiplierPreset: (value: number) => void
}

export default function RecipeIngredientsSection({
  ingredients,
  multiplier,
  multiplierInput,
  isIngredientBookmarked,
  onToggleIngredient,
  onMultiplierInputChange,
  onMultiplierPreset,
}: RecipeIngredientsSectionProps) {
  const grouped = groupIngredients(ingredients)

  return (
    <section>
      <h2 className="mb-3 text-lg font-semibold">材料</h2>
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="text-sm text-muted-foreground">分量</span>
        {MULTIPLIER_PRESETS.map(v => (
          <Button
            key={v}
            type="button"
            variant={multiplier === v ? 'default' : 'outline'}
            size="sm"
            onClick={() => onMultiplierPreset(v)}
          >
            {v}倍
          </Button>
        ))}
        <Input
          type="number"
          step="0.1"
          min="0.1"
          value={multiplierInput}
          onChange={e => onMultiplierInputChange(e.target.value)}
          className="w-20"
        />
        <span className="text-sm text-muted-foreground">倍</span>
      </div>
      {grouped.map(([groupName, items], gi) => (
        <div key={gi} className="mb-3">
          {groupName && <h3 className="my-2 font-semibold">{groupName}</h3>}
          <ul className="flex flex-col gap-1.5">
            {items.map(ing => (
              <li key={ing.id} className="flex items-baseline gap-1.5">
                <button
                  type="button"
                  onClick={() => onToggleIngredient(ing.name)}
                  title={isIngredientBookmarked(ing.name) ? 'ブックマーク解除' : 'ブックマークする'}
                  className="shrink-0"
                >
                  <Star
                    className={cn(
                      'h-4 w-4',
                      isIngredientBookmarked(ing.name)
                        ? 'fill-primary text-primary'
                        : 'text-muted-foreground/40'
                    )}
                  />
                </button>
                <span className="text-sm">
                  <Link
                    to={`/?q=${encodeURIComponent(ing.name)}`}
                    className="underline decoration-muted-foreground/40 underline-offset-2"
                  >
                    {ing.name}
                  </Link>
                  {(ing.quantity || ing.unit) && (
                    <>
                      {' '}
                      {scaleQuantity(ing.quantity, multiplier)}
                      {ing.unit ?? ''}
                    </>
                  )}
                  {ing.note && <span className="text-muted-foreground">（{ing.note}）</span>}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  )
}
