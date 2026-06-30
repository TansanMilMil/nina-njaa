import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { importRecipeFromUrl, DuplicateUrlError } from '../api'
import { toast } from 'sonner'
import RobotLoading from '../components/RobotLoading'

function extractUrl(text: string): string | null {
  const match = text.match(/https?:\/\/[^\s]+/i)
  return match ? match[0] : null
}

export default function SharePage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const startedRef = useRef(false)

  useEffect(() => {
    if (startedRef.current) return
    startedRef.current = true

    const rawUrl = searchParams.get('url')?.trim()
    const text = searchParams.get('text')?.trim()
    const shared = rawUrl || (text ? extractUrl(text) ?? text : null)

    if (!shared) {
      setError('共有されたURLが取得できませんでした')
      setLoading(false)
      return
    }

    const normalizedUrl = /^https?:\/\//i.test(shared) ? shared : `https://${shared}`

    importRecipeFromUrl(normalizedUrl)
      .then(recipe => {
        toast.success(`「${recipe.name}」を登録しました`)
        navigate(`/recipe/${recipe.id}`)
      })
      .catch(err => {
        if (err instanceof DuplicateUrlError) {
          setError('このURLのレシピはすでに登録されています')
        } else if (err instanceof Error) {
          setError(err.message)
        } else {
          setError('レシピの生成に失敗しました')
        }
        setLoading(false)
      })
  }, [searchParams, navigate])

  if (loading) {
    return <RobotLoading label="レシピを生成しています" />
  }

  return (
    <div className="flex flex-col items-center gap-4 py-12 text-center">
      {error && <p className="text-sm text-destructive">{error}</p>}
      <Link to="/" className="text-sm text-primary underline">
        トップページへ戻る
      </Link>
    </div>
  )
}
