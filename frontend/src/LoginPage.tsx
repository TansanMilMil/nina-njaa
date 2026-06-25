import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'

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
    <main className="mx-auto mt-16 w-full max-w-xs px-4">
      <Card>
        <CardHeader>
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
            />
            <Input
              type="password"
              placeholder="パスワード"
              value={pass}
              onChange={e => setPass(e.target.value)}
            />
            <Button type="submit">ログイン</Button>
            {error && (
              <p className="text-center text-sm text-destructive">{error}</p>
            )}
          </form>
        </CardContent>
      </Card>
    </main>
  )
}
