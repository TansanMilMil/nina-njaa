import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { importRecipeFromUrl, DuplicateUrlError } from '../api'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface Props {
  onSuccess?: () => void
}

export default function ImportFromUrl({ onSuccess }: Props) {
  const [url, setUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return
    setError(null)
    setLoading(true)
    try {
      const recipe = await importRecipeFromUrl(url.trim())
      setUrl('')
      onSuccess?.()
      navigate(`/recipe/${recipe.id}`)
    } catch (err) {
      if (err instanceof DuplicateUrlError) {
        setError('このURLのレシピはすでに登録されています')
      } else if (err instanceof Error) {
        setError(err.message)
      } else {
        setError('レシピの生成に失敗しました')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="https://example.com/recipe/..."
          disabled={loading}
          required
          autoFocus
          className="flex-1"
        />
        <Button type="submit" disabled={loading || !url.trim()} className="whitespace-nowrap">
          {loading ? '生成中...' : 'レシピを生成'}
        </Button>
      </form>
      {error && <p className="mt-2 text-sm text-destructive">{error}</p>}
    </div>
  )
}
