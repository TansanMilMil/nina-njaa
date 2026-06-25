import { Link } from 'react-router-dom'
import type { Recipe } from '../api'

interface RecipeCardProps {
  recipe: Recipe
  isBookmarked?: boolean
}

export default function RecipeCard({ recipe, isBookmarked }: RecipeCardProps) {
  return (
    <Link
      to={`/recipe/${recipe.id}`}
      style={{
        display: 'block',
        padding: '0.55rem 0.75rem',
        border: `1px solid ${isBookmarked ? '#f0a500' : '#ddd'}`,
        borderRadius: '8px',
        textDecoration: 'none',
        color: 'inherit',
        background: isBookmarked ? '#fffbf0' : '#fff'
      }}
    >
      <div>
        <span style={{ fontSize: '0.95rem', fontWeight: 600 }}>{recipe.name}</span>
        {isBookmarked && (
          <span
            title="ブックマーク済み"
            style={{ marginLeft: '0.4rem', color: '#f0a500', fontSize: '1rem' }}
          >
            ★
          </span>
        )}
      </div>
      {recipe.ingredient_names && recipe.ingredient_names.length > 0 && (
        <div
          style={{
            marginTop: '0.2rem',
            fontSize: '0.78rem',
            color: '#888',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {recipe.ingredient_names.join('・')}
        </div>
      )}
    </Link>
  )
}
