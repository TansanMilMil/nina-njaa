import { useState, useEffect } from 'react'
import { getRecipe, recordRecipeViewed, getCookedLogForRecipe } from '../api'
import type { RecipeDetail, CookedLogEntry } from '../api'
import { useCurrentUser } from '../contexts/UserContext'

export function useRecipeDetail(id: string | undefined) {
  const currentUsername = useCurrentUser()
  const [recipe, setRecipe] = useState<RecipeDetail | null>(null)
  const [error, setError] = useState(false)
  const [cookedLog, setCookedLog] = useState<CookedLogEntry | null>(null)

  useEffect(() => {
    if (!id) return
    let cancelled = false
    setRecipe(null)
    setError(false)
    getRecipe(Number(id))
      .then(data => {
        if (!cancelled) {
          setRecipe(data)
          recordRecipeViewed(Number(id)).catch(() => {})
          if (currentUsername) {
            getCookedLogForRecipe(Number(id)).then(log => {
              if (!cancelled) setCookedLog(log)
            }).catch(() => {})
          }
        }
      })
      .catch(() => {
        if (!cancelled) setError(true)
      })
    return () => { cancelled = true }
  }, [id, currentUsername])

  const refreshCookedLog = () => {
    if (!id) return
    getCookedLogForRecipe(Number(id)).then(log => setCookedLog(log)).catch(() => {})
  }

  return { recipe, setRecipe, error, cookedLog, refreshCookedLog }
}
