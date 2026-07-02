import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, Trash2, Edit2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { getCookedLogEntries, getCookedLogForRecipe, deleteCookedLogEntry, updateCookedLogEntry } from '../api'
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
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editMemo, setEditMemo] = useState('')

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

  const handleEditStart = (entry: CookedLogRawEntry) => {
    setEditingId(entry.id)
    setEditMemo(entry.memo ?? '')
  }

  const handleEditSave = async (entryId: number) => {
    try {
      await updateCookedLogEntry(recipe_id, entryId, editMemo)
      setEntries(prev =>
        prev.map(e => (e.id === entryId ? { ...e, memo: editMemo || null } : e))
      )
      setEditingId(null)
      toast.success('更新しました')
    } catch {
      toast.error('更新に失敗しました')
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
              className="flex items-start justify-between rounded-lg border bg-card px-4 py-3 text-card-foreground shadow-sm"
            >
              {editingId === entry.id ? (
                <div className="flex w-full flex-col gap-2">
                  <span className="text-sm font-medium">{formatDateTime(entry.cooked_at)}</span>
                  <textarea
                    className="w-full rounded-md border bg-transparent px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    rows={3}
                    value={editMemo}
                    onChange={e => setEditMemo(e.target.value)}
                    placeholder="メモ（任意）"
                  />
                  <div className="flex justify-end gap-2">
                    <Button variant="outline" size="sm" onClick={() => setEditingId(null)}>
                      キャンセル
                    </Button>
                    <Button size="sm" onClick={() => handleEditSave(entry.id)}>
                      保存
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex flex-1 flex-col gap-1 pr-4">
                    <span className="text-sm font-medium">{formatDateTime(entry.cooked_at)}</span>
                    {entry.memo && (
                      <p className="text-sm text-muted-foreground whitespace-pre-wrap">
                        {entry.memo}
                      </p>
                    )}
                  </div>
                  <div className="flex shrink-0 -mr-2 -mt-1 items-center gap-1">
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleEditStart(entry)}
                      aria-label="編集"
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDelete(entry.id)}
                      aria-label="削除"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
