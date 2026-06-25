import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { importRecipeFromUrl, DuplicateUrlError } from '../api'

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
      <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '0.5rem' }}>
        <input
          type="url"
          value={url}
          onChange={e => setUrl(e.target.value)}
          placeholder="https://example.com/recipe/..."
          disabled={loading}
          required
          autoFocus
          style={{
            flex: 1,
            padding: '0.5rem 0.75rem',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            fontSize: '0.9rem',
            outline: 'none',
          }}
        />
        <button
          type="submit"
          disabled={loading || !url.trim()}
          style={{
            padding: '0.5rem 1rem',
            background: loading ? '#9ca3af' : '#f0a500',
            color: '#fff',
            border: 'none',
            borderRadius: '6px',
            fontWeight: 600,
            fontSize: '0.9rem',
            cursor: loading ? 'not-allowed' : 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          {loading ? '生成中...' : 'レシピを生成'}
        </button>
      </form>
      {error && (
        <p style={{ margin: '0.5rem 0 0', color: '#dc2626', fontSize: '0.85rem' }}>{error}</p>
      )}
    </div>
  )
}
