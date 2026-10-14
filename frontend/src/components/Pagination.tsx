import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Button } from './ui/button'

type Props = {
  page: number
  totalPages: number
  onChange: (page: number) => void
}

export default function Pagination({ page, totalPages, onChange }: Props) {
  if (totalPages <= 1) return null

  return (
    <nav className="flex items-center justify-center gap-3" aria-label="ページネーション">
      <Button
        variant="outline"
        size="icon"
        onClick={() => onChange(page - 1)}
        disabled={page <= 1}
        aria-label="前のページ"
      >
        <ChevronLeft className="h-4 w-4" />
      </Button>
      <span className="text-sm tabular-nums text-muted-foreground">
        {page} / {totalPages}
      </span>
      <Button
        variant="outline"
        size="icon"
        onClick={() => onChange(page + 1)}
        disabled={page >= totalPages}
        aria-label="次のページ"
      >
        <ChevronRight className="h-4 w-4" />
      </Button>
    </nav>
  )
}
