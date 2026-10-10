import { useEffect, useRef, useState } from 'react'
import { Input } from '@/components/ui/input'

const DEBOUNCE_MS = 300

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
}

export default function SearchBar({ value, onChange }: SearchBarProps) {
  const [draft, setDraft] = useState(value)
  const lastEmitted = useRef(value)
  const timer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const onChangeRef = useRef(onChange)

  useEffect(() => {
    onChangeRef.current = onChange
  })

  // URL側の更新はtransition扱いで遅延するため、inputはローカルstateで制御しないとIME変換中の文字が巻き戻って重複する
  useEffect(() => {
    if (value === lastEmitted.current) return
    clearTimeout(timer.current)
    lastEmitted.current = value
    setDraft(value)
  }, [value])

  useEffect(() => () => clearTimeout(timer.current), [])

  const handleChange = (next: string) => {
    setDraft(next)
    clearTimeout(timer.current)
    timer.current = setTimeout(() => {
      lastEmitted.current = next
      onChangeRef.current(next)
    }, DEBOUNCE_MS)
  }

  return (
    <Input
      type="search"
      value={draft}
      onChange={e => handleChange(e.target.value)}
      placeholder="レシピ名・食材名で検索"
      className="h-11 text-base"
    />
  )
}
