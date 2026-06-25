import { useState, useEffect, useCallback } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import SearchPage from './pages/SearchPage'
import RecipePage from './pages/RecipePage'
import BookmarksPage from './pages/BookmarksPage'
import LoginPage from './LoginPage'
import ImportFromUrl from './components/ImportFromUrl'
import { getCredentials, saveCredentials } from './api'

export default function App() {
  const [authed, setAuthed] = useState(() => getCredentials() !== null)
  const [importOpen, setImportOpen] = useState(false)

  useEffect(() => {
    const handleUnauthorized = () => setAuthed(false)
    window.addEventListener('unauthorized', handleUnauthorized)
    return () => window.removeEventListener('unauthorized', handleUnauthorized)
  }, [])

  useEffect(() => {
    if (!importOpen) return
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setImportOpen(false)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [importOpen])

  const handleLogin = (user: string, pass: string) => {
    saveCredentials(user, pass)
    setAuthed(true)
  }

  const handleImportSuccess = useCallback(() => {
    setImportOpen(false)
  }, [])

  if (!authed) {
    return <LoginPage onLogin={handleLogin} />
  }

  return (
    <BrowserRouter>
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
        <header
          style={{
            flexShrink: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '1rem 1.5rem',
            borderBottom: '1px solid #eee',
            background: '#fff'
          }}
        >
          <Link
            to="/"
            style={{
              fontSize: '1.4rem',
              fontWeight: 700,
              textDecoration: 'none',
              color: '#f0a500'
            }}
          >
            Ninanjaa
          </Link>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <button
              onClick={() => setImportOpen(true)}
              style={{
                padding: '0.4rem 0.9rem',
                background: '#f0a500',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer',
              }}
            >
              レシピ登録
            </button>
            <Link to="/bookmarks" style={{ textDecoration: 'none', color: '#333' }}>
              ブックマーク
            </Link>
          </div>
        </header>
        <main style={{ flex: 1, overflowY: 'auto', maxWidth: '720px', width: '100%', margin: '0 auto', padding: '1.5rem', boxSizing: 'border-box' }}>
          <Routes>
            <Route path="/" element={<SearchPage />} />
            <Route path="/recipe/:id" element={<RecipePage />} />
            <Route path="/bookmarks" element={<BookmarksPage />} />
          </Routes>
        </main>
      </div>

      {importOpen && (
        <div
          onClick={() => setImportOpen(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.4)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 100,
          }}
        >
          <div
            onClick={e => e.stopPropagation()}
            style={{
              background: '#fff',
              borderRadius: '12px',
              padding: '1.5rem',
              width: '100%',
              maxWidth: '520px',
              margin: '0 1rem',
              boxShadow: '0 8px 32px rgba(0,0,0,0.18)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <p style={{ margin: 0, fontWeight: 600, fontSize: '1rem', color: '#333' }}>
                URLからレシピを登録
              </p>
              <button
                onClick={() => setImportOpen(false)}
                style={{
                  background: 'none',
                  border: 'none',
                  fontSize: '1.2rem',
                  cursor: 'pointer',
                  color: '#6b7280',
                  lineHeight: 1,
                  padding: '0.2rem',
                }}
              >
                ✕
              </button>
            </div>
            <ImportFromUrl onSuccess={handleImportSuccess} />
          </div>
        </div>
      )}
    </BrowserRouter>
  )
}
