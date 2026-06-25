import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

interface LoginPageProps {
  onLogin: (user: string, pass: string) => void | Promise<void>
  error?: string | null
  loading?: boolean
}

export default function LoginPage({ onLogin, error, loading }: LoginPageProps) {
  const [user, setUser] = useState('')
  const [pass, setPass] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onLogin(user, pass)
  }

  return (
    <main className="mx-auto mt-16 w-full max-w-xs px-4">
      <Card>
        <CardHeader className="items-center">
          <img src="/nina-njaa-icon.png" alt="Ninanjaa" className="mb-1 h-16 w-16" />
          <CardTitle className="text-center text-2xl text-primary">Ninanjaa</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <Input
              type="text"
              placeholder="ユーザー名"
              value={user}
              onChange={e => setUser(e.target.value)}
              autoFocus
              disabled={loading}
            />
            <Input
              type="password"
              placeholder="パスワード"
              value={pass}
              onChange={e => setPass(e.target.value)}
              disabled={loading}
            />
            <Button type="submit" disabled={loading}>
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'ログイン'}
            </Button>
            {error && (
              <p className="text-center text-sm text-destructive">{error}</p>
            )}
          </form>
        </CardContent>
      </Card>
    </main>
  )
}
