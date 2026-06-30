import { useState } from 'react'
import { Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import RecipeCard from '../components/RecipeCard'
import { suggestRecipes } from '../api'
import type { SuggestResult } from '../api'

const EXAMPLE_QUERIES = [
  '鶏肉があります',
  'さっぱりしたもの食べたい',
  '時間がない',
  '野菜をたくさん使いたい',
  '子どもが喜ぶもの',
]

export default function SuggestPage() {
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<SuggestResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async () => {
    if (!query.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      setResult(await suggestRecipes(query.trim()))
    } catch (e) {
      setError(e instanceof Error ? e.message : '提案の取得に失敗しました')
    } finally {
      setLoading(false)
    }
  }

  const handleChipClick = (q: string) => {
    setQuery(prev => (prev ? `${prev}、${q}` : q))
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-primary" />
        <h1 className="text-xl font-bold">AIレシピ提案</h1>
      </div>

      <div className="space-y-3">
        <textarea
          placeholder="食材や気分を教えてください"
          value={query}
          onChange={e => setQuery(e.target.value)}
          rows={3}
          onKeyDown={e => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit()
          }}
          className="w-full resize-none rounded-md border border-input bg-background px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
        />
        <div className="flex flex-wrap gap-2">
          {EXAMPLE_QUERIES.map(q => (
            <button
              key={q}
              type="button"
              onClick={() => handleChipClick(q)}
              className="rounded-full border px-3 py-1 text-xs text-muted-foreground hover:bg-accent"
            >
              {q}
            </button>
          ))}
        </div>
        <Button
          onClick={handleSubmit}
          disabled={loading || !query.trim()}
          className="w-full"
        >
          {loading ? '考え中...' : 'おすすめを聞く'}
        </Button>
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {result && (
        <div className="space-y-4">
          <p className="rounded-lg bg-muted px-4 py-3 text-sm">{result.comment}</p>
          {result.recipes.length === 0 ? (
            <p className="text-sm text-muted-foreground">条件に合うレシピが見つかりませんでした。</p>
          ) : (
            <div className="space-y-3">
              {result.recipes.map(r => (
                <RecipeCard key={r.id} recipe={r} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
