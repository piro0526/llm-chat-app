'use client'

import { useParams, useRouter } from 'next/navigation'
import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import { ChatInterfaceWithSessions } from '@/components/chat/chat-interface-with-sessions'
import { ArrowLeft, LogOut } from 'lucide-react'

export default function ProjectPage() {
  const params = useParams()
  const router = useRouter()
  const { user, logout } = useAuth()
  const projectId = params?.projectId as string

  useEffect(() => {
    if (!user) {
      router.push('/')
    }
  }, [user, router])

  const handleBack = () => {
    router.push('/dashboard')
  }

  if (!user) {
    return <div>Loading...</div>
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleBack}
                className="flex items-center"
              >
                <ArrowLeft className="h-4 w-4 mr-2" />
                プロジェクト一覧に戻る
              </Button>
              <h1 className="text-2xl font-bold text-gray-900">
                LLM Chat App
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">{user?.email}</span>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4 mr-2" />
                ログアウト
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <ChatInterfaceWithSessions projectId={projectId} />
      </main>
    </div>
  )
}