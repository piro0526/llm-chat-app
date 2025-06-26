'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import { ProjectList } from './project-list'
import { ChatInterfaceWithSessions } from '@/components/chat/chat-interface-with-sessions'
import { LLMSettings } from './llm-settings'
import { LogOut, MessageSquare, FolderOpen, Settings } from 'lucide-react'

type View = 'projects' | 'chat' | 'settings'

export function Dashboard() {
  const [currentView, setCurrentView] = useState<View>('projects')
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null)
  const { user, logout } = useAuth()

  const handleProjectSelect = (projectId: string) => {
    setSelectedProjectId(projectId)
    setCurrentView('chat')
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
                {selectedProjectId && (
                  <Button
                    variant={currentView === 'chat' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setCurrentView('chat')}
                  >
                    <MessageSquare className="h-4 w-4 mr-2" />
                    チャット
                  </Button>
                )}
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
        {currentView === 'chat' && selectedProjectId && (
          <ChatInterfaceWithSessions projectId={selectedProjectId} />
        )}
        {currentView === 'settings' && <LLMSettings />}
      </main>
    </div>
  )
}