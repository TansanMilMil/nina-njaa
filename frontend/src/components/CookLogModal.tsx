import { Button } from '@/components/ui/button'

interface CookLogModalProps {
  memo: string
  submitting: boolean
  onMemoChange: (value: string) => void
  onSubmit: () => void
  onClose: () => void
}

export default function CookLogModal({ memo, submitting, onMemoChange, onSubmit, onClose }: CookLogModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
        <h2 className="mb-4 text-xl font-bold">料理記録の追加</h2>
        <textarea
          className="mb-4 w-full rounded-md border bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
          rows={4}
          placeholder="メモ（任意）&#13;&#10;例：塩を少し減らしてちょうどよかった"
          value={memo}
          onChange={e => onMemoChange(e.target.value)}
          disabled={submitting}
        />
        <div className="flex justify-end gap-3">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={submitting}
          >
            キャンセル
          </Button>
          <Button onClick={onSubmit} disabled={submitting}>
            {submitting ? '記録中...' : '記録する'}
          </Button>
        </div>
      </div>
    </div>
  )
}
