import { Check, Tag } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import type { Category } from '../api'

interface Props {
  categories: Category[]
  selectedIds: number[]
  onToggle: (id: number) => void
}

export default function CategoryFilter({ categories, selectedIds, onToggle }: Props) {
  if (categories.length === 0) return null
  return (
    <div className="flex flex-col gap-1">
      <span className="flex items-center gap-1 text-xs text-muted-foreground">
        <Tag className="h-3 w-3" />
        カテゴリ
      </span>
      <div className="flex flex-wrap gap-1.5">
        {categories.map(c => {
          const selected = selectedIds.includes(c.id)
          return (
            <Badge
              key={c.id}
              variant={selected ? 'default' : 'outline'}
              onClick={() => onToggle(c.id)}
              className="cursor-pointer gap-1 rounded-md border-dashed"
            >
              {selected && <Check className="h-3 w-3" />}
              {c.name}
            </Badge>
          )
        })}
      </div>
    </div>
  )
}
