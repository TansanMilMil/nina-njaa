interface BookmarkButtonProps {
  isBookmarked: boolean
  onToggle: () => void
}

export default function BookmarkButton({ isBookmarked, onToggle }: BookmarkButtonProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      style={{
        padding: '0.5rem 1rem',
        fontSize: '1rem',
        cursor: 'pointer',
        border: '1px solid #f0a500',
        borderRadius: '6px',
        background: isBookmarked ? '#f0a500' : '#fff',
        color: isBookmarked ? '#fff' : '#f0a500'
      }}
    >
      {isBookmarked ? '★ ブックマーク解除' : '☆ ブックマークする'}
    </button>
  )
}
