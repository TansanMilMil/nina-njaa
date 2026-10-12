import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { GOOGLE_LOGIN_URL } from './api'

interface LoginPageProps {
  error?: string | null
}

export default function LoginPage({ error }: LoginPageProps) {
  return (
    <main className="mx-auto mt-16 w-full max-w-xs px-4">
      <Card>
        <CardHeader className="items-center">
          <img src="/nina-njaa-icon.png" alt="Ninanjaa" className="mb-1 h-16 w-16" />
          <CardTitle className="text-center text-2xl text-primary">Ninanjaa</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <Button asChild>
            <a href={GOOGLE_LOGIN_URL}>Googleでログイン</a>
          </Button>
          {error && (
            <p className="text-center text-sm text-destructive">{error}</p>
          )}
        </CardContent>
      </Card>
    </main>
  )
}
