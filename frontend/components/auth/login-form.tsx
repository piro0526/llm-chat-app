'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'

export function LoginForm() {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, register } = useAuth()
  const { toast } = useToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      if (isLogin) {
        await login(email, password)
        toast({
          title: "ログイン成功",
          description: "ダッシュボードにリダイレクトしています...",
        })
      } else {
        await register(email, password)
        toast({
          title: "アカウント作成成功",
          description: "ログインが完了しました。",
        })
      }
    } catch (error: any) {
      console.error('Authentication error:', error)
      
      let errorMessage = "認証に失敗しました"
      
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      } else if (error.response?.status === 422) {
        errorMessage = "入力内容に問題があります。メールアドレスとパスワードを確認してください。"
      } else if (error.response?.status === 500) {
        errorMessage = "サーバーエラーが発生しました。しばらく待ってから再試行してください。"
      } else if (error.message) {
        errorMessage = error.message
      }
      
      toast({
        title: "エラー",
        description: errorMessage,
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">
            {isLogin ? 'ログイン' : 'アカウント作成'}
          </CardTitle>
          <CardDescription className="text-center">
            {isLogin 
              ? 'アカウントにログインしてください'
              : '新しいアカウントを作成してください'
            }
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Input
                type="email"
                placeholder="メールアドレス"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div>
              <Input
                type="password"
                placeholder="パスワード"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading 
                ? (isLogin ? 'ログイン中...' : 'アカウント作成中...') 
                : (isLogin ? 'ログイン' : 'アカウント作成')
              }
            </Button>
          </form>
          <div className="mt-4 text-center">
            <Button
              variant="link"
              onClick={() => setIsLogin(!isLogin)}
              className="text-sm"
            >
              {isLogin 
                ? 'アカウントをお持ちでない方はこちら'
                : 'すでにアカウントをお持ちの方はこちら'
              }
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}