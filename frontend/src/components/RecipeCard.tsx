import { Link } from 'react-router-dom'
import type { Recipe } from '../api'

interface RecipeCardProps {
  recipe: Recipe
}

export default function RecipeCard({ recipe }: RecipeCardProps) {
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
    </Link>
  )
}
