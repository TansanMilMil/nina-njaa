import '../skeleton.css'

function SkeletonBox({ width = '100%', height = '1rem', style }: {
  width?: string | number
  height?: string | number
  style?: React.CSSProperties
}) {
  return (
    <div
      className="skeleton"
      style={{ width, height, flexShrink: 0, ...style }}
    />
  )
}

export function RecipeCardSkeleton() {
  return (
    <div style={{
      padding: '0.55rem 0.75rem',
      border: '1px solid #ddd',
      borderRadius: '8px',
      background: '#fff',
      display: 'flex',
      flexDirection: 'column',
      gap: '0.45rem',
    }}>
      <SkeletonBox width="62%" height="0.95rem" />
      <SkeletonBox width="85%" height="0.7rem" />
    </div>
  )
}

export function RecipePageSkeleton() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
      <SkeletonBox width="72%" height="1.8rem" />
      <SkeletonBox width="7rem" height="2rem" style={{ borderRadius: '6px' }} />
      <SkeletonBox width="11rem" height="0.9rem" />
      <SkeletonBox width="5rem" height="0.9rem" />

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <SkeletonBox width="3rem" height="1.2rem" />
        {[75, 60, 80, 55, 70].map((w, i) => (
          <SkeletonBox key={i} width={`${w}%`} height="0.9rem" />
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
        <SkeletonBox width="3.5rem" height="1.2rem" />
        {[90, 78, 85, 70].map((w, i) => (
          <SkeletonBox key={i} width={`${w}%`} height="0.9rem" />
        ))}
      </div>
    </div>
  )
}
