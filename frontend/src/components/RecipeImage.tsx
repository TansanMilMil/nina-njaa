import { UtensilsCrossed } from 'lucide-react'
import { cn } from '@/lib/utils'

interface RecipeImageProps {
  imagePath?: string | null
  alt?: string | null
  className?: string
  iconClassName?: string
}

export default function RecipeImage({ imagePath, alt, className, iconClassName }: RecipeImageProps) {
  if (imagePath) {
    return <img src={`/uploads/${imagePath}`} alt={alt ?? ''} className={cn('object-cover', className)} />
  }
  return (
    <div
      role="img"
      aria-label="画像なし"
      className={cn('flex items-center justify-center bg-muted text-muted-foreground/60', className)}
    >
      <UtensilsCrossed className={cn('h-8 w-8', iconClassName)} />
    </div>
  )
}
