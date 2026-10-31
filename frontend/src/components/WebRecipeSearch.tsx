import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { toast } from 'sonner'
import { ChevronDown, ChevronUp, ExternalLink, Globe, Plus } from 'lucide-react'
import { Button } from '@/components/ui/button'
import RobotLoading from './RobotLoading'
import { createRecipe, DuplicateUrlError, searchWebRecipes } from '../api'
import type { WebRecipe } from '../api'

interface Props {
  query: string
}

function hostname(url: string): string {
  try {
    return new URL(url).hostname
  } catch {
    return url
  }
}

function WebRecipeCard({ recipe }: { recipe: WebRecipe }) {
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [saving, setSaving] = useState(false)
  const { registered_recipe_id: registeredId, ...payload } = recipe

  const handleRegister = async () => {
    setSaving(true)
    try {
      const created = await createRecipe(payload)
      toast.success(`「${created.name}」を登録しました`)
      navigate(`/recipe/${created.id}`)
    } catch (e) {
      toast.error(e instanceof DuplicateUrlError ? e.message : '登録に失敗しました')
      setSaving(false)
    }
  }

  return (
    <div className="rounded-lg border bg-card px-3 py-2.5 text-card-foreground shadow-xs">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-semibold">{recipe.name}</div>
          <a
            href={recipe.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-0.5 inline-flex max-w-full items-center gap-1 text-xs text-primary hover:underline"
          >
            <ExternalLink className="h-3 w-3 shrink-0" />
            <span className="truncate">{hostname(recipe.source_url)}</span>
          </a>
        </div>
        {registeredId !== null ? (
          <Button asChild size="sm" variant="secondary" className="shrink-0">
            <Link to={`/recipe/${registeredId}`}>登録済み</Link>
          </Button>
        ) : (
          <Button size="sm" onClick={handleRegister} disabled={saving} className="shrink-0 gap-1">
            <Plus className="h-3.5 w-3.5" />
            {saving ? '登録中…' : '登録'}
          </Button>
        )}
      </div>
      <div className="mt-1 truncate text-xs text-muted-foreground">
        {recipe.ingredients.map(i => i.name).join('・')}
      </div>
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className="mt-1 inline-flex items-center gap-0.5 text-xs text-muted-foreground hover:text-foreground"
      >
        {open ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
        {open ? '閉じる' : '材料と手順を見る'}
      </button>
      {open && (
        <div className="mt-2 space-y-2 text-xs">
          {recipe.servings && <p className="text-muted-foreground">{recipe.servings}人分</p>}
          <ul className="space-y-0.5">
            {recipe.ingredients.map((ing, i) => (
              <li key={i} className="flex justify-between gap-2 border-b border-dashed py-0.5">
                <span>{ing.group_name ? `[${ing.group_name}] ` : ''}{ing.name}</span>
                <span className="shrink-0 text-muted-foreground">{[ing.quantity, ing.unit].filter(Boolean).join('')}</span>
              </li>
            ))}
          </ul>
          {recipe.steps.length > 0 && (
            <ol className="list-decimal space-y-1 pl-4">
              {recipe.steps.map(st => <li key={st.step_number}>{st.description}</li>)}
            </ol>
          )}
        </div>
      )}
    </div>
  )
}

export default function WebRecipeSearch({ query }: Props) {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<WebRecipe[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSearch = async () => {
    setLoading(true)
    setError(null)
    try {
      setResults(await searchWebRecipes(query))
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Web検索に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {results === null && !loading && (
        <Button variant="outline" onClick={handleSearch} className="w-full gap-1.5">
          <Globe className="h-4 w-4" />
          Webで検索
        </Button>
      )}
      {loading && <RobotLoading label="Webでレシピを探しています" />}
      {error && <p className="text-sm text-destructive">{error}</p>}
      {results !== null && (
        <div className="flex flex-col gap-3">
          <h2 className="flex items-center gap-1.5 text-lg font-semibold">
            <Globe className="h-4 w-4" />
            Webで見つかったレシピ
          </h2>
          {results.length === 0 ? (
            <p className="text-sm text-muted-foreground">Webでレシピが見つかりませんでした</p>
          ) : (
            results.map(r => <WebRecipeCard key={r.source_url} recipe={r} />)
          )}
        </div>
      )}
    </div>
  )
}
