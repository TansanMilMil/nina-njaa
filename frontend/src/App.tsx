import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import SearchPage from './pages/SearchPage'
import RecipePage from './pages/RecipePage'
import BookmarksPage from './pages/BookmarksPage'
import LoginPage from './LoginPage'
import { getCredentials, saveCredentials } from './api'

export default function App() {
  const [authed, setAuthed] = useState(() => getCredentials() !== null)

  useEffect(() => {
    const handleUnauthorized = () => setAuthed(false)
    window.addEventListener('unauthorized', handleUnauthorized)
    return () => window.removeEventListener('unauthorized', handleUnauthorized)
  }, [])

  const handleLogin = (user: string, pass: string) => {
    saveCredentials(user, pass)
    setAuthed(true)
  }

  if (!authed) {
    return <LoginPage onLogin={handleLogin} />
  }

  return (
    <BrowserRouter>
      <header
        style={{
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
        <Link to="/bookmarks" style={{ textDecoration: 'none', color: '#333' }}>
          ブックマーク
        </Link>
      </header>
      <main style={{ maxWidth: '720px', margin: '0 auto', padding: '1.5rem' }}>
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/recipe/:id" element={<RecipePage />} />
          <Route path="/bookmarks" element={<BookmarksPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
