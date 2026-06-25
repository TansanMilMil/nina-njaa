import { cn } from '@/lib/utils'

function SkeletonBox({ className }: { className?: string }) {
  return <div className={cn('animate-pulse rounded-md bg-muted', className)} />
}

export function RecipeCardSkeleton() {
  return (
    <div className="flex flex-col gap-2 rounded-lg border p-2.5">
      <SkeletonBox className="h-4 w-3/5" />
      <SkeletonBox className="h-3 w-5/6" />
    </div>
  )
}

export function RecipePageSkeleton() {
  return (
    <div className="flex flex-col gap-5">
      <SkeletonBox className="h-7 w-3/4" />
      <SkeletonBox className="h-9 w-28" />
      <SkeletonBox className="h-4 w-44" />
      <SkeletonBox className="h-4 w-20" />

      <div className="flex flex-col gap-2.5">
        <SkeletonBox className="h-5 w-12" />
        {['w-3/4', 'w-3/5', 'w-4/5', 'w-1/2', 'w-2/3'].map((w, i) => (
          <SkeletonBox key={i} className={cn('h-4', w)} />
        ))}
      </div>

      <div className="flex flex-col gap-2.5">
        <SkeletonBox className="h-5 w-14" />
        {['w-11/12', 'w-3/4', 'w-5/6', 'w-2/3'].map((w, i) => (
          <SkeletonBox key={i} className={cn('h-4', w)} />
        ))}
      </div>
    </div>
  )
}
