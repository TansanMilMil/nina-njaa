import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { getCookedLogEntries, getCookedLogForRecipe, deleteCookedLogEntry } from '../api'
import type { CookedLogRawEntry, CookedLogEntry } from '../api'

function formatDateTime(isoString: string): string {
  const d = new Date(isoString)
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${yyyy}/${mm}/${dd} ${hh}:${min}`
}

export default function CookedLogDetailPage() {
  const { recipeId } = useParams<{ recipeId: string }>()
  const navigate = useNavigate()
  const recipe_id = parseInt(recipeId ?? '', 10)

  const [entries, setEntries] = useState<CookedLogRawEntry[]>([])
  const [summary, setSummary] = useState<CookedLogEntry | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      getCookedLogEntries(recipe_id),
      getCookedLogForRecipe(recipe_id),
    ]).then(([entryList, entrySummary]) => {
      setEntries(entryList)
      setSummary(entrySummary)
      setLoading(false)
    })
  }, [recipe_id])

  const handleDelete = async (entryId: number) => {
    const prev = entries
    setEntries(prev.filter(e => e.id !== entryId))
    try {
      await deleteCookedLogEntry(recipe_id, entryId)
      toast.success('削除しました')
    } catch {
      setEntries(prev)
      toast.error('削除に失敗しました')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => navigate('/cooked-logs')}
          aria-label="戻る"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <h1 className="flex-1 truncate text-2xl font-bold">
          {summary?.recipe_name ?? `レシピ #${recipe_id}`}
        </h1>
        <Link
          to={`/recipe/${recipe_id}`}
          className="shrink-0 text-sm text-primary hover:underline"
        >
          レシピを見る
        </Link>
      </div>

      {loading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }, (_, i) => (
            <div key={i} className="h-10 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : entries.length === 0 ? (
        <p className="text-sm text-muted-foreground">記録がありません</p>
      ) : (
        <div className="flex flex-col gap-2">
          {entries.map(entry => (
            <div
              key={entry.id}
              className="flex items-center justify-between rounded-lg border bg-card px-4 py-2 text-card-foreground shadow-sm"
            >
              <span className="text-sm">{formatDateTime(entry.cooked_at)}</span>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => handleDelete(entry.id)}
                aria-label="削除"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
