import { useState, useEffect, useContext } from 'react'
import { Link } from 'react-router-dom'
import { UserContext } from '../contexts/UserContext'
import { getCookedLogs } from '../api'
import type { CookedLogEntry, CookedLogSort } from '../api'

function formatDate(isoString: string): string {
  const d = new Date(isoString)
  return `${d.getFullYear()}/${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
}

export default function CookedLogsPage() {
  const currentUsername = useContext(UserContext)
  const [logs, setLogs] = useState<CookedLogEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [sortOrder, setSortOrder] = useState<CookedLogSort>('last_cooked_at_desc')

  useEffect(() => {
    if (currentUsername) {
      setLoading(true)
      getCookedLogs(sortOrder).then(data => {
        setLogs(data)
        setLoading(false)
      })
    } else {
      setLogs([])
      setLoading(false)
    }
  }, [currentUsername, sortOrder])

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">料理記録</h1>
        {!loading && logs.length > 0 && (
          <select
            value={sortOrder}
            onChange={e => setSortOrder(e.target.value as CookedLogSort)}
            className="rounded-md border bg-card px-2 py-1 text-sm text-card-foreground"
          >
            <option value="last_cooked_at_desc">最終調理日が新しい順</option>
            <option value="count_desc">調理回数が多い順</option>
          </select>
        )}
      </div>

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
            <Link
              key={entry.recipe_id}
              to={`/cooked-logs/${entry.recipe_id}`}
              className="flex items-center justify-between rounded-lg border bg-card text-card-foreground shadow-sm transition-colors hover:bg-accent"
            >
              {entry.image_path && (
                <img
                  src={`/uploads/${entry.image_path}`}
                  alt={entry.recipe_name ?? ''}
                  className="h-20 w-20 shrink-0 rounded-l-lg object-cover"
                />
              )}
              <span className={`flex-1 font-medium ${entry.image_path ? 'px-3 py-3' : 'px-4 py-3'}`}>
                {entry.recipe_name ?? `レシピ #${entry.recipe_id}`}
              </span>
              <div className="flex shrink-0 flex-col items-end gap-0.5 px-4 py-3 text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">{entry.count}回</span>
                <span>最終: {formatDate(entry.last_cooked_at)}</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
