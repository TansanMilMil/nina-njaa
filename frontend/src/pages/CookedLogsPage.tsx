import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getCookedLogs } from '../api'
import type { CookedLogEntry } from '../api'

function formatDate(isoString: string): string {
  const d = new Date(isoString)
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
}

export default function CookedLogsPage() {
  const [logs, setLogs] = useState<CookedLogEntry[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getCookedLogs().then(data => {
      setLogs(data)
      setLoading(false)
    })
  }, [])

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold">料理記録</h1>

      {loading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }, (_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-muted" />
          ))}
        </div>
      ) : logs.length === 0 ? (
        <p className="text-sm text-muted-foreground">まだ料理記録がありません</p>
      ) : (
        <div className="flex flex-col gap-2">
          {logs.map(entry => (
            <div
              key={entry.recipe_id}
              className="flex items-center justify-between rounded-lg border bg-card px-4 py-3"
            >
              <Link
                to={`/recipe/${entry.recipe_id}`}
                className="font-medium hover:underline"
              >
                {entry.recipe_name ?? `レシピ #${entry.recipe_id}`}
              </Link>
              <div className="flex flex-col items-end gap-0.5 text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">{entry.count}回</span>
                <span>最終: {formatDate(entry.last_cooked_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
