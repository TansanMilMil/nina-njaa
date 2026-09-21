import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { createRecipe } from '../api'
import { toast } from 'sonner'
import RecipeStepsEditor, { createStepId } from '@/components/RecipeStepsEditor'
import type { RecipeStep } from '@/components/RecipeStepsEditor'

interface FormIngredient {
  group_name: string
  name: string
  quantity: string
  unit: string
  note: string
}

const emptyIngredient = (): FormIngredient => ({
  group_name: '',
  name: '',
  quantity: '',
  unit: '',
  note: '',
})

export default function AddRecipePage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [servings, setServings] = useState('')
  const [ingredients, setIngredients] = useState<FormIngredient[]>([emptyIngredient()])
  const [steps, setSteps] = useState<RecipeStep[]>([{ id: createStepId(), description: '' }])
  const [saving, setSaving] = useState(false)

  function updateIngredient(index: number, field: keyof FormIngredient, value: string) {
    setIngredients(prev => {
      const next = [...prev]
      next[index] = { ...next[index], [field]: value }
      return next
    })
  }

  function addIngredient() {
    setIngredients(prev => [...prev, emptyIngredient()])
  }

  function removeIngredient(index: number) {
    setIngredients(prev => prev.filter((_, i) => i !== index))
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!name.trim()) {
      toast.error('レシピ名を入力してください')
      return
    }
    setSaving(true)
    try {
      const recipe = await createRecipe({
        name: name.trim(),
        source_url: sourceUrl.trim() || null,
        servings: servings !== '' ? Number(servings) : null,
        ingredients: ingredients
          .filter(ing => ing.name.trim())
          .map((ing, i) => ({
            group_name: ing.group_name.trim() || null,
            name: ing.name.trim(),
            quantity: ing.quantity.trim() || null,
            unit: ing.unit.trim() || null,
            note: ing.note.trim() || null,
            sort_order: i,
          })),
        steps: steps
          .filter(s => s.description.trim())
          .map((s, i) => ({
            step_number: i + 1,
            description: s.description.trim(),
          })),
      })
      toast.success('レシピを登録しました！')
      navigate(`/recipe/${recipe.id}`)
    } catch {
      toast.error('登録に失敗しました')
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      <h1 className="text-2xl font-bold">レシピを追加</h1>

      <label className="flex flex-col gap-1">
        <span className="text-sm font-medium">レシピ名 <span className="text-destructive">*</span></span>
        <Input
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="例：鶏の唐揚げ"
          required
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-sm font-medium">元レシピURL（任意）</span>
        <Input
          value={sourceUrl}
          onChange={e => setSourceUrl(e.target.value)}
          placeholder="https://..."
          type="url"
        />
      </label>

      <label className="flex flex-col gap-1">
        <span className="text-sm font-medium">人数（任意）</span>
        <Input
          type="number"
          min={1}
          value={servings}
          onChange={e => setServings(e.target.value)}
          className="w-24"
          placeholder="2"
        />
      </label>

      <section>
        <h2 className="mb-3 text-lg font-semibold">材料</h2>
        {ingredients.map((ing, i) => (
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
            <Button type="button" variant="ghost" size="sm" onClick={() => removeIngredient(i)}>削除</Button>
          </div>
        ))}
        <Button type="button" variant="outline" size="sm" onClick={addIngredient}>+ 材料を追加</Button>
      </section>

      <RecipeStepsEditor
        steps={steps}
        onStepsChange={setSteps}
        stepPlaceholder={i => `手順 ${i + 1}`}
      />

      <div className="flex justify-end gap-2 pt-2">
        <Button type="button" variant="outline" onClick={() => navigate(-1)} disabled={saving}>
          キャンセル
        </Button>
        <Button type="submit" disabled={saving}>
          {saving ? '登録中...' : '登録する'}
        </Button>
      </div>
    </form>
  )
}
