import { Input } from '@/components/ui/input'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
}

export default function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <Input
      type="search"
      value={value}
      onChange={e => onChange(e.target.value)}
      placeholder="レシピ名・食材名で検索"
      className="h-11 text-base"
    />
  )
}
