import { useState, useEffect } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { Star } from 'lucide-react'
import { getRecipe, updateRecipe, recordRecipeViewed, deleteRecipe } from '../api'
import type { RecipeDetail, Ingredient } from '../api'
import BookmarkButton from '../components/BookmarkButton'
import { RecipePageSkeleton } from '../components/Skeleton'
import { useBookmarks } from '../hooks/useBookmarks'
import { useIngredientBookmarks } from '../hooks/useIngredientBookmarks'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { cn } from '@/lib/utils'

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
  const [deleting, setDeleting] = useState(false)
  const navigate = useNavigate()
  const { isBookmarked, toggle } = useBookmarks()
  const { isIngredientBookmarked, toggleIngredient } = useIngredientBookmarks()

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

  async function handleDelete() {
    if (!id || !window.confirm(`「${recipe?.name}」を削除しますか？`)) return
    setDeleting(true)
    try {
      await deleteRecipe(Number(id))
      navigate('/')
    } catch {
      alert('削除に失敗しました')
      setDeleting(false)
    }
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

  if (error) return <p className="text-muted-foreground">レシピが見つかりませんでした</p>
  if (!recipe) return <RecipePageSkeleton />

  if (isEditing && editState) {
    return (
      <article className="flex flex-col gap-5">
        <div className="flex items-center gap-2">
          <h1 className="flex-1 text-2xl font-bold">編集</h1>
          <Button variant="destructive" size="sm" onClick={handleDelete} disabled={saving || deleting}>
            {deleting ? '削除中...' : '削除'}
          </Button>
          <Button variant="outline" size="sm" onClick={cancelEditing} disabled={saving || deleting}>
            キャンセル
          </Button>
          <Button size="sm" onClick={saveEditing} disabled={saving || deleting}>
            {saving ? '保存中...' : '保存'}
          </Button>
        </div>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">レシピ名</span>
          <Input value={editState.name} onChange={e => updateField('name', e.target.value)} />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">元レシピURL</span>
          <Input value={editState.source_url} onChange={e => updateField('source_url', e.target.value)} />
        </label>

        <label className="flex flex-col gap-1">
          <span className="text-sm font-medium">人数</span>
          <Input
            type="number"
            value={editState.servings}
            onChange={e => updateField('servings', e.target.value)}
            className="w-24"
          />
        </label>

        <section>
          <h2 className="mb-3 text-lg font-semibold">材料</h2>
          {editState.ingredients.map((ing, i) => (
            <div key={i} className="mb-2 flex flex-wrap items-center gap-2">
              <Input
                placeholder="グループ名"
                value={ing.group_name}
                onChange={e => updateIngredient(i, 'group_name', e.target.value)}
                className="w-28"
              />
              <Input
                placeholder="材料名"
                value={ing.name}
                onChange={e => updateIngredient(i, 'name', e.target.value)}
                className="min-w-28 flex-1"
              />
              <Input
                placeholder="分量"
                value={ing.quantity}
                onChange={e => updateIngredient(i, 'quantity', e.target.value)}
                className="w-20"
              />
              <Input
                placeholder="単位"
                value={ing.unit}
                onChange={e => updateIngredient(i, 'unit', e.target.value)}
                className="w-16"
              />
              <Input
                placeholder="備考"
                value={ing.note}
                onChange={e => updateIngredient(i, 'note', e.target.value)}
                className="w-28"
              />
              <Button variant="ghost" size="sm" onClick={() => removeIngredient(i)}>削除</Button>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={addIngredient}>+ 材料を追加</Button>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold">作り方</h2>
          {editState.steps.map((step, i) => (
            <div key={i} className="mb-2 flex items-start gap-2">
              <span className="min-w-6 pt-1.5 text-sm">{i + 1}.</span>
              <textarea
                value={step.description}
                onChange={e => updateStep(i, e.target.value)}
                rows={2}
                className="flex w-full flex-1 rounded-md border border-input bg-transparent px-3 py-1.5 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
              />
              <Button variant="ghost" size="sm" onClick={() => removeStep(i)}>削除</Button>
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={addStep}>+ 手順を追加</Button>
        </section>
      </article>
    )
  }

  const grouped = groupIngredients(recipe.ingredients)

  return (
    <article className="flex flex-col gap-5">
      <div className="flex items-center gap-4">
        <h1 className="flex-1 text-2xl font-bold">{recipe.name}</h1>
        <Button variant="outline" size="sm" onClick={startEditing}>編集</Button>
      </div>

      <BookmarkButton
        isBookmarked={isBookmarked(recipe.id)}
        onToggle={() => toggle(recipe.id)}
      />

      <p>
        <a
          href={recipe.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary underline-offset-4 hover:underline"
        >
          元レシピを見る
        </a>
      </p>

      {recipe.servings && <p className="text-sm">人数：{recipe.servings}</p>}

      <section>
        <h2 className="mb-3 text-lg font-semibold">材料</h2>
        {grouped.map(([groupName, items], gi) => (
          <div key={gi} className="mb-3">
            {groupName && <h3 className="my-2 font-semibold">{groupName}</h3>}
            <ul className="flex flex-col gap-1.5">
              {items.map(ing => (
                <li key={ing.id} className="flex items-baseline gap-1.5">
                  <button
                    type="button"
                    onClick={() => toggleIngredient(ing.name)}
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
                        {ing.quantity ?? ''}
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

      <section>
        <h2 className="mb-3 text-lg font-semibold">作り方</h2>
        <ol className="flex list-decimal flex-col gap-2 pl-5 text-sm">
          {recipe.steps.map(step => (
            <li key={step.id}>{step.description}</li>
          ))}
        </ol>
      </section>
    </article>
  )
}
