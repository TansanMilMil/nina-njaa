import { useState, useEffect, useCallback, useRef } from 'react'
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import { X, PlusCircle, Bookmark, Menu, LogOut, Clock } from 'lucide-react'
import SearchPage from './pages/SearchPage'
import RecipePage from './pages/RecipePage'
import BookmarksPage from './pages/BookmarksPage'
import HistoryPage from './pages/HistoryPage'
import LoginPage from './LoginPage'
import ImportFromUrl from './components/ImportFromUrl'
import { Button } from '@/components/ui/button'
import { login, logout, checkAuth } from './api'

export default function App() {
  const [authed, setAuthed] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loginLoading, setLoginLoading] = useState(false)
  const [loginError, setLoginError] = useState<string | null>(null)
  const [importOpen, setImportOpen] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    checkAuth().then(username => {
      setAuthed(username !== null)
      setLoading(false)
    })
  }, [])

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

  useEffect(() => {
    if (!menuOpen) return
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false)
      }
    }
    window.addEventListener('mousedown', handleClickOutside)
    return () => window.removeEventListener('mousedown', handleClickOutside)
  }, [menuOpen])

  const handleLogin = async (user: string, pass: string) => {
    setLoginLoading(true)
    try {
      await login(user, pass)
      setAuthed(true)
      setLoginError(null)
    } catch {
      setLoginError('ユーザー名またはパスワードが違います')
    } finally {
      setLoginLoading(false)
    }
  }

  const handleLogout = async () => {
    await logout()
    setAuthed(false)
    setMenuOpen(false)
  }

  const handleImportSuccess = useCallback(() => {
    setImportOpen(false)
  }, [])

  if (loading) {
    return null
  }

  if (!authed) {
    return <LoginPage onLogin={handleLogin} error={loginError} loading={loginLoading} />
  }

  return (
    <BrowserRouter>
      <div className="flex h-full flex-col">
        <header className="flex flex-shrink-0 items-center justify-between border-b bg-background px-6 py-4">
          <Link to="/" className="text-2xl font-bold text-primary">
            Ninanjaa
          </Link>
          <div className="flex items-center gap-2">
            <Button
              size="icon"
              variant="ghost"
              onClick={() => setImportOpen(true)}
              aria-label="レシピ登録"
            >
              <PlusCircle className="h-5 w-5" />
            </Button>
            <Button size="icon" variant="ghost" asChild aria-label="ブックマーク">
              <Link to="/bookmarks">
                <Bookmark className="h-5 w-5" />
              </Link>
            </Button>
            <div ref={menuRef} className="relative">
              <Button
                size="icon"
                variant="ghost"
                onClick={() => setMenuOpen(o => !o)}
                aria-label="メニュー"
              >
                <Menu className="h-5 w-5" />
              </Button>
              {menuOpen && (
                <div className="absolute right-0 top-full mt-1 w-44 rounded-lg border bg-card shadow-lg z-10">
                  <Link
                    to="/history"
                    onClick={() => setMenuOpen(false)}
                    className="flex w-full items-center gap-2 px-4 py-2 text-sm hover:bg-muted rounded-t-lg"
                  >
                    <Clock className="h-4 w-4" />
                    最近見たもの
                  </Link>
                  <button
                    type="button"
                    onClick={handleLogout}
                    className="flex w-full items-center gap-2 px-4 py-2 text-sm hover:bg-muted rounded-b-lg"
                  >
                    <LogOut className="h-4 w-4" />
                    ログアウト
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-3xl p-6">
            <Routes>
              <Route path="/" element={<SearchPage />} />
              <Route path="/recipe/:id" element={<RecipePage />} />
              <Route path="/bookmarks" element={<BookmarksPage />} />
              <Route path="/history" element={<HistoryPage />} />
            </Routes>
          </div>
        </main>
      </div>

      {importOpen && (
        <div
          onClick={() => setImportOpen(false)}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
        >
          <div
            onClick={e => e.stopPropagation()}
            className="mx-4 w-full max-w-lg rounded-xl border bg-card p-6 shadow-lg"
          >
            <div className="mb-4 flex items-center justify-between">
              <p className="font-semibold">URLからレシピを登録</p>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setImportOpen(false)}
                aria-label="閉じる"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <ImportFromUrl onSuccess={handleImportSuccess} />
          </div>
        </div>
      )}
    </BrowserRouter>
  )
}
