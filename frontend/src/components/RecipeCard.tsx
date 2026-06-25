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
        padding: '1rem',
        border: '1px solid #ddd',
        borderRadius: '8px',
        textDecoration: 'none',
        color: 'inherit',
        background: '#fff'
      }}
    >
      <span style={{ fontSize: '1.1rem', fontWeight: 600 }}>{recipe.name}</span>
      {isBookmarked && (
        <span
          title="ブックマーク済み"
          style={{ marginLeft: '0.4rem', color: '#f0a500', fontSize: '1rem' }}
        >
          ★
        </span>
      )}
    </Link>
  )
}
