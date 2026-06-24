import RecipeCard from '../components/RecipeCard'
import { useBookmarks } from '../hooks/useBookmarks'

export default function BookmarksPage() {
  const { bookmarks } = useBookmarks()

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <h1 style={{ margin: 0, fontSize: '1.4rem' }}>ブックマーク</h1>
      {bookmarks.length === 0 ? (
        <p>ブックマークはまだありません</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          {bookmarks.map(b => (
            <RecipeCard
              key={b.id}
              recipe={{
                id: b.id,
                name: b.name,
                source_url: '',
                servings: null,
                scraped_at: null
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}
