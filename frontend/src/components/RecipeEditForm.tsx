import { useState } from 'react'
import type { ChangeEvent } from 'react'
import { X } from 'lucide-react'
import { updateRecipe } from '../api'
import type { RecipeDetail } from '../api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import RecipeStepsEditor, { createStepId } from '@/components/RecipeStepsEditor'
import type { RecipeStep } from '@/components/RecipeStepsEditor'

interface EditIngredient {
  group_name: string
  name: string
  quantity: string
  unit: string
  note: string
}

interface EditState {
  name: string
  source_url: string
  servings: string
  ingredients: EditIngredient[]
  steps: RecipeStep[]
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
    steps: recipe.steps.map(step => ({ id: createStepId(), description: step.description ?? '' })),
  }
}

interface RecipeEditFormProps {
  recipe: RecipeDetail
  recipeId: string
  imageUploading: boolean
  deleting: boolean
  onImageUpload: (e: ChangeEvent<HTMLInputElement>) => void
  onDeleteImage: () => void
  onSaved: (updated: RecipeDetail) => void
  onCancel: () => void
  onDelete: () => void
}

export default function RecipeEditForm({
  recipe,
  recipeId,
  imageUploading,
  deleting,
  onImageUpload,
  onDeleteImage,
  onSaved,
  onCancel,
  onDelete,
}: RecipeEditFormProps) {
  const [editState, setEditState] = useState<EditState>(() => recipeToEditState(recipe))
  const [saving, setSaving] = useState(false)

  async function saveEditing() {
    setSaving(true)
    try {
      const updated = await updateRecipe(Number(recipeId), {
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
      onSaved(updated)
    } catch {
      alert('保存に失敗しました')
    } finally {
      setSaving(false)
    }
  }

  function updateField<K extends keyof EditState>(key: K, value: EditState[K]) {
    setEditState(prev => ({ ...prev, [key]: value }))
  }

  function updateIngredient(index: number, field: keyof EditIngredient, value: string) {
    setEditState(prev => {
      const ingredients = [...prev.ingredients]
      ingredients[index] = { ...ingredients[index], [field]: value }
      return { ...prev, ingredients }
    })
  }

  function addIngredient() {
    setEditState(prev => ({
      ...prev,
      ingredients: [...prev.ingredients, { group_name: '', name: '', quantity: '', unit: '', note: '' }],
    }))
  }

  function removeIngredient(index: number) {
    setEditState(prev => ({ ...prev, ingredients: prev.ingredients.filter((_, i) => i !== index) }))
  }

  return (
    <article className="flex flex-col gap-5">
      <div className="flex items-center gap-2">
        <h1 className="flex-1 text-2xl font-bold">編集</h1>
        <Button variant="destructive" size="sm" onClick={onDelete} disabled={saving || deleting}>
          {deleting ? '削除中...' : '削除'}
        </Button>
        <Button variant="outline" size="sm" onClick={onCancel} disabled={saving || deleting}>
          キャンセル
        </Button>
        <Button size="sm" onClick={saveEditing} disabled={saving || deleting}>
          {saving ? '保存中...' : '保存'}
        </Button>
      </div>

      {recipe.image_path ? (
        <div className="relative">
          <img
            src={`/uploads/${recipe.image_path}`}
            alt={recipe.name ?? ''}
            className="w-full rounded-lg object-cover max-h-64"
          />
          <button
            type="button"
            onClick={onDeleteImage}
            className="absolute top-2 right-2 rounded-full bg-black/50 p-1 text-white hover:bg-black/70"
            aria-label="画像を削除"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ) : (
        <label className="flex cursor-pointer items-center justify-center gap-2 rounded-lg border-2 border-dashed border-muted py-6 text-sm text-muted-foreground hover:border-primary hover:text-primary">
          <input type="file" accept="image/*" className="hidden" onChange={onImageUpload} disabled={imageUploading} />
          {imageUploading ? 'アップロード中...' : '画像を追加'}
        </label>
      )}

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

      <RecipeStepsEditor
        steps={editState.steps}
        onStepsChange={steps => updateField('steps', steps)}
      />
    </article>
  )
}
