import { Star } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface BookmarkButtonProps {
  isBookmarked: boolean
  onToggle: () => void
}

export default function BookmarkButton({ isBookmarked, onToggle }: BookmarkButtonProps) {
  return (
    <Button
      type="button"
      size="icon"
      variant={isBookmarked ? 'default' : 'outline'}
      onClick={onToggle}
      aria-label={isBookmarked ? 'ブックマーク解除' : 'ブックマークする'}
      className={isBookmarked ? '' : 'border-primary text-primary hover:text-primary'}
    >
      <Star className={isBookmarked ? 'fill-current' : ''} />
    </Button>
  )
}
