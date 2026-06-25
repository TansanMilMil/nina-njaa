import { useState } from 'react'

interface LoginPageProps {
  onLogin: (user: string, pass: string) => void | Promise<void>
  error?: string | null
}

export default function LoginPage({ onLogin, error }: LoginPageProps) {
  const [user, setUser] = useState('')
  const [pass, setPass] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onLogin(user, pass)
  }

  return (
    <main style={{ maxWidth: '320px', margin: '4rem auto', padding: '1.5rem' }}>
      <h1 style={{ fontSize: '1.4rem', color: '#f0a500', textAlign: 'center' }}>Ninanjaa</h1>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        <input
          type="text"
          placeholder="ユーザー名"
          value={user}
          onChange={e => setUser(e.target.value)}
          autoFocus
          style={{ padding: '0.5rem', fontSize: '1rem' }}
        />
        <input
          type="password"
          placeholder="パスワード"
          value={pass}
          onChange={e => setPass(e.target.value)}
          style={{ padding: '0.5rem', fontSize: '1rem' }}
        />
        <button
          type="submit"
          style={{
            padding: '0.5rem',
            fontSize: '1rem',
            background: '#f0a500',
            color: '#fff',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer'
          }}
        >
          ログイン
        </button>
        {error && (
          <p style={{ margin: 0, color: '#d33', fontSize: '0.9rem', textAlign: 'center' }}>
            {error}
          </p>
        )}
      </form>
    </main>
  )
}
