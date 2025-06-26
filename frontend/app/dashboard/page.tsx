'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import { ProjectList } from '@/components/dashboard/project-list'
import { LLMSettings } from '@/components/dashboard/llm-settings'
import { LogOut, FolderOpen, Settings } from 'lucide-react'

type View = 'projects' | 'settings'

export default function DashboardPage() {
  const [currentView, setCurrentView] = useState<View>('projects')
  const { user, logout } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!user) {
      router.push('/')
    }
  }, [user, router])

  const handleProjectSelect = (projectId: string) => {
    router.push(`/projects/${projectId}`)
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
              <h1 className="text-2xl font-bold text-gray-900">
                LLM Chat App
              </h1>
              <nav className="flex space-x-2">
                <Button
                  variant={currentView === 'projects' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setCurrentView('projects')}
                >
                  <FolderOpen className="h-4 w-4 mr-2" />
                  プロジェクト
                </Button>
                <Button
                  variant={currentView === 'settings' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setCurrentView('settings')}
                >
                  <Settings className="h-4 w-4 mr-2" />
                  設定
                </Button>
              </nav>
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
        {currentView === 'projects' && (
          <ProjectList onProjectSelect={handleProjectSelect} />
        )}
        {currentView === 'settings' && <LLMSettings />}
      </main>
    </div>
  )
}