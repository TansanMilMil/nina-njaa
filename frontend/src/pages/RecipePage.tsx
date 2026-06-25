import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getRecipe, updateRecipe, recordRecipeViewed } from '../api'
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

interface EditIngredient {
  group_name: string
  name: string
  quantity: string
  unit: string
  note: string
}

interface EditStep {
  description: string
}

interface EditState {
  name: string
  source_url: string
  servings: string
  ingredients: EditIngredient[]
  steps: EditStep[]
}

function recipeToEditState(recipe: RecipeDetail): EditState {
  return {
    name: recipe.name ?? '',
    source_url: recipe.source_url ?? '',
    servings: recipe.servings != null ? String(recipe.servings) : '',
    ingredients: recipe.ingredients.map(ing => ({
      group_name: ing.group_name ?? '',
      name: ing.name ?? '',
      quantity: ing.quantity ?? '',
      unit: ing.unit ?? '',
      note: ing.note ?? '',
    })),
    steps: recipe.steps.map(step => ({ description: step.description ?? '' })),
  }
}

export default function RecipePage() {
  const { id } = useParams<{ id: string }>()
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null)
  const [error, setError] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editState, setEditState] = useState<EditState | null>(null)
  const [saving, setSaving] = useState(false)
  const { isBookmarked, toggle } = useBookmarks()

  useEffect(() => {
    if (!id) return
    let cancelled = false
    setRecipe(null)
    setError(false)
    setIsEditing(false)
    getRecipe(Number(id))
      .then(data => {
        if (!cancelled) {
          setRecipe(data)
          recordRecipeViewed(Number(id)).catch(() => {})
        }
      })
      .catch(() => {
        if (!cancelled) setError(true)
      })
    return () => { cancelled = true }
  }, [id])

  function startEditing() {
    if (!recipe) return
    setEditState(recipeToEditState(recipe))
    setIsEditing(true)
  }

  function cancelEditing() {
    setIsEditing(false)
    setEditState(null)
  }

  async function saveEditing() {
    if (!editState || !id) return
    setSaving(true)
    try {
      const updated = await updateRecipe(Number(id), {
        name: editState.name,
        source_url: editState.source_url,
        servings: editState.servings !== '' ? Number(editState.servings) : null,
        ingredients: editState.ingredients.map((ing, i) => ({
          group_name: ing.group_name || null,
          name: ing.name,
          quantity: ing.quantity || null,
          unit: ing.unit || null,
          note: ing.note || null,
          sort_order: i,
        })),
        steps: editState.steps.map((step, i) => ({
          step_number: i + 1,
          description: step.description,
        })),
      })
      setRecipe(updated)
      setIsEditing(false)
      setEditState(null)
    } catch {
      alert('保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  function updateField<K extends keyof EditState>(key: K, value: EditState[K]) {
    setEditState(prev => prev ? { ...prev, [key]: value } : prev)
  }

  function updateIngredient(index: number, field: keyof EditIngredient, value: string) {
    setEditState(prev => {
      if (!prev) return prev
      const ingredients = [...prev.ingredients]
      ingredients[index] = { ...ingredients[index], [field]: value }
      return { ...prev, ingredients }
    })
  }

  function addIngredient() {
    setEditState(prev => {
      if (!prev) return prev
      return {
        ...prev,
        ingredients: [...prev.ingredients, { group_name: '', name: '', quantity: '', unit: '', note: '' }],
      }
    })
  }

  function removeIngredient(index: number) {
    setEditState(prev => {
      if (!prev) return prev
      return { ...prev, ingredients: prev.ingredients.filter((_, i) => i !== index) }
    })
  }

  function updateStep(index: number, value: string) {
    setEditState(prev => {
      if (!prev) return prev
      const steps = [...prev.steps]
      steps[index] = { description: value }
      return { ...prev, steps }
    })
  }

  function addStep() {
    setEditState(prev => {
      if (!prev) return prev
      return { ...prev, steps: [...prev.steps, { description: '' }] }
    })
  }

  function removeStep(index: number) {
    setEditState(prev => {
      if (!prev) return prev
      return { ...prev, steps: prev.steps.filter((_, i) => i !== index) }
    })
  }

  if (error) return <p>レシピが見つかりませんでした</p>
  if (!recipe) return <p>読み込み中...</p>

  if (isEditing && editState) {
    return (
      <article style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <h1 style={{ margin: 0, flex: 1 }}>編集</h1>
          <button onClick={cancelEditing} disabled={saving}>キャンセル</button>
          <button onClick={saveEditing} disabled={saving}>{saving ? '保存中...' : '保存'}</button>
        </div>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <span>レシピ名</span>
          <input value={editState.name} onChange={e => updateField('name', e.target.value)} />
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <span>元レシピURL</span>
          <input value={editState.source_url} onChange={e => updateField('source_url', e.target.value)} />
        </label>

        <label style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
          <span>人数</span>
          <input
            type="number"
            value={editState.servings}
            onChange={e => updateField('servings', e.target.value)}
            style={{ width: '6rem' }}
          />
        </label>

        <section>
          <h2 style={{ fontSize: '1.2rem' }}>材料</h2>
          {editState.ingredients.map((ing, i) => (
            <div key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap' }}>
              <input
                placeholder="グループ名"
                value={ing.group_name}
                onChange={e => updateIngredient(i, 'group_name', e.target.value)}
                style={{ width: '7rem' }}
              />
              <input
                placeholder="材料名"
                value={ing.name}
                onChange={e => updateIngredient(i, 'name', e.target.value)}
                style={{ flex: 1, minWidth: '7rem' }}
              />
              <input
                placeholder="分量"
                value={ing.quantity}
                onChange={e => updateIngredient(i, 'quantity', e.target.value)}
                style={{ width: '5rem' }}
              />
              <input
                placeholder="単位"
                value={ing.unit}
                onChange={e => updateIngredient(i, 'unit', e.target.value)}
                style={{ width: '4rem' }}
              />
              <input
                placeholder="備考"
                value={ing.note}
                onChange={e => updateIngredient(i, 'note', e.target.value)}
                style={{ width: '7rem' }}
              />
              <button onClick={() => removeIngredient(i)}>削除</button>
            </div>
          ))}
          <button onClick={addIngredient}>+ 材料を追加</button>
        </section>

        <section>
          <h2 style={{ fontSize: '1.2rem' }}>作り方</h2>
          {editState.steps.map((step, i) => (
            <div key={i} style={{ display: 'flex', gap: '0.5rem', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
              <span style={{ paddingTop: '0.35rem', minWidth: '1.5rem' }}>{i + 1}.</span>
              <textarea
                value={step.description}
                onChange={e => updateStep(i, e.target.value)}
                rows={2}
                style={{ flex: 1 }}
              />
              <button onClick={() => removeStep(i)}>削除</button>
            </div>
          ))}
          <button onClick={addStep}>+ 手順を追加</button>
        </section>
      </article>
    )
  }

  const grouped = groupIngredients(recipe.ingredients)

  return (
    <article style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <h1 style={{ margin: 0, flex: 1 }}>{recipe.name}</h1>
        <button onClick={startEditing}>編集</button>
      </div>

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
                  <Link to={`/?q=${encodeURIComponent(ing.name)}`} style={{ color: 'inherit', textDecoration: 'underline', textDecorationColor: '#ccc', textUnderlineOffset: '2px' }}>
                    {ing.name}
                  </Link>
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
