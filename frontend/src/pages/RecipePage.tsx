import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { getRecipe } from '../api'
import type { RecipeDetail, Ingredient } from '../api'
import BookmarkButton from '../components/BookmarkButton'
import { useBookmarks } from '../hooks/useBookmarks'

function groupIngredients(ingredients: Ingredient[]): [string | null, Ingredient[]][] {
  const groups: [string | null, Ingredient[]][] = []
  for (const ing of ingredients) {
    const key = ing.group_name ?? null
    const last = groups[groups.length - 1]
    if (last && last[0] === key) {
      last[1].push(ing)
    } else {
      groups.push([key, [ing]])
    }
  }
  return groups
}

export default function RecipePage() {
  const { id } = useParams<{ id: string }>()
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null)
  const [error, setError] = useState(false)
  const { isBookmarked, toggle } = useBookmarks()

  useEffect(() => {
    if (!id) return
    let cancelled = false
    setRecipe(null)
    setError(false)
    getRecipe(Number(id))
      .then(data => {
        if (!cancelled) setRecipe(data)
      })
      .catch(() => {
        if (!cancelled) setError(true)
      })
    return () => {
      cancelled = true
    }
  }, [id])

  if (error) return <p>レシピが見つかりませんでした</p>
  if (!recipe) return <p>読み込み中...</p>

  const grouped = groupIngredients(recipe.ingredients)

  return (
    <article style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <h1 style={{ margin: 0 }}>{recipe.name}</h1>

      <BookmarkButton
        isBookmarked={isBookmarked(recipe.id)}
        onToggle={() => toggle({ id: recipe.id, name: recipe.name })}
      />

      <p style={{ margin: 0 }}>
        <a href={recipe.source_url} target="_blank" rel="noopener noreferrer">
          元レシピを見る
        </a>
      </p>

      {recipe.servings && <p style={{ margin: 0 }}>人数：{recipe.servings}</p>}

      <section>
        <h2 style={{ fontSize: '1.2rem' }}>材料</h2>
        {grouped.map(([groupName, items], gi) => (
          <div key={gi} style={{ marginBottom: '0.75rem' }}>
            {groupName && <h3 style={{ fontSize: '1rem', margin: '0.5rem 0' }}>{groupName}</h3>}
            <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
              {items.map(ing => (
                <li key={ing.id}>
                  {ing.name}
                  {(ing.quantity || ing.unit) && (
                    <>
                      {' '}
                      {ing.quantity ?? ''}
                      {ing.unit ?? ''}
                    </>
                  )}
                  {ing.note && <span style={{ color: '#888' }}>（{ing.note}）</span>}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </section>

      <section>
        <h2 style={{ fontSize: '1.2rem' }}>作り方</h2>
        <ol style={{ margin: 0, paddingLeft: '1.25rem', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {recipe.steps.map(step => (
            <li key={step.id}>{step.description}</li>
          ))}
        </ol>
      </section>
    </article>
  )
}
