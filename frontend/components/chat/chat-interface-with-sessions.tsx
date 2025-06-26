'use client'

import { useState, useEffect, useRef } from 'react'
import { chatApi, chatSessionsApi, llmSettingsApi, projectsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { Send, Plus, Trash2, Bot, User, MessageSquare, Edit2, FolderOpen, Menu, X } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github.css'

interface ChatLog {
  id: string
  session_id: string
  role: string
  content: string
  created_at: string
}

interface ChatSession {
  id: string
  project_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview?: string
}

interface LLMSetting {
  provider: string
  model: string
}

interface Project {
  id: string
  title: string
  description?: string
}

interface ChatInterfaceWithSessionsProps {
  projectId: string
}

export function ChatInterfaceWithSessions({ projectId }: ChatInterfaceWithSessionsProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatLog[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionsLoading, setSessionsLoading] = useState(true)
  const [llmSettings, setLlmSettings] = useState<LLMSetting[]>([])
  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const [project, setProject] = useState<Project | null>(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  useEffect(() => {
    fetchProject()
    fetchSessions()
    fetchLLMSettings()
  }, [projectId])

  useEffect(() => {
    if (selectedSessionId) {
      fetchMessages(selectedSessionId)
    }
  }, [selectedSessionId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchProject = async () => {
    try {
      const response = await projectsApi.getById(projectId)
      setProject(response.data)
    } catch (error) {
      toast({
        title: "エラー",
        description: "プロジェクト情報の取得に失敗しました",
        variant: "destructive",
      })
    }
  }

  const fetchSessions = async () => {
    try {
      const response = await chatSessionsApi.getAll(projectId)
      setSessions(response.data)
      
      // Auto-select first session if none selected
      if (response.data.length > 0 && !selectedSessionId) {
        setSelectedSessionId(response.data[0].id)
      }
    } catch (error) {
      toast({
        title: "エラー",
        description: "会話セッションの取得に失敗しました",
        variant: "destructive",
      })
    } finally {
      setSessionsLoading(false)
    }
  }

  const fetchMessages = async (sessionId: string) => {
    try {
      const response = await chatApi.getHistory(sessionId)
      setMessages(response.data)
    } catch (error) {
      toast({
        title: "エラー",
        description: "メッセージ履歴の取得に失敗しました",
        variant: "destructive",
      })
    }
  }

  const fetchLLMSettings = async () => {
    try {
      const response = await llmSettingsApi.getAll()
      setLlmSettings(response.data)
      if (response.data.length > 0) {
        setSelectedProvider(response.data[0].provider)
        setSelectedModel(response.data[0].model)
      }
    } catch (error) {
      console.error('Failed to fetch LLM settings:', error)
    }
  }

  const createNewSession = async () => {
    try {
      const response = await chatSessionsApi.create(projectId, { title: "New Chat" })
      const newSession = response.data
      setSessions([newSession, ...sessions])
      setSelectedSessionId(newSession.id)
      setMessages([])
      toast({
        title: "新しい会話",
        description: "新しい会話セッションを作成しました",
      })
    } catch (error) {
      toast({
        title: "エラー",
        description: "新しい会話の作成に失敗しました",
        variant: "destructive",
      })
    }
  }

  const deleteSession = async (sessionId: string) => {
    if (!confirm('この会話を削除しますか？')) return

    try {
      await chatSessionsApi.delete(projectId, sessionId)
      setSessions(sessions.filter(s => s.id !== sessionId))
      
      if (selectedSessionId === sessionId) {
        const remainingSessions = sessions.filter(s => s.id !== sessionId)
        if (remainingSessions.length > 0) {
          setSelectedSessionId(remainingSessions[0].id)
        } else {
          setSelectedSessionId(null)
          setMessages([])
        }
      }
      
      toast({
        title: "会話削除",
        description: "会話を削除しました",
      })
    } catch (error) {
      toast({
        title: "エラー",
        description: "会話の削除に失敗しました",
        variant: "destructive",
      })
    }
  }

  const updateSessionTitle = async (sessionId: string, newTitle: string) => {
    try {
      await chatSessionsApi.update(projectId, sessionId, { title: newTitle })
      setSessions(sessions.map(s => 
        s.id === sessionId ? { ...s, title: newTitle } : s
      ))
      setEditingSessionId(null)
      setEditingTitle('')
    } catch (error) {
      toast({
        title: "エラー",
        description: "タイトルの更新に失敗しました",
        variant: "destructive",
      })
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || !selectedSessionId || !selectedProvider) return

    const userMessage = newMessage.trim()
    setNewMessage('')
    setLoading(true)

    // Add user message to UI immediately
    const tempUserMessage: ChatLog = {
      id: 'temp-user',
      session_id: selectedSessionId,
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempUserMessage])

    try {
      const response = await chatApi.send({
        message: userMessage,
        session_id: selectedSessionId,
        provider: selectedProvider,
        model: selectedModel,
      })

      // Remove temp message and add actual messages
      setMessages(prev => {
        const filtered = prev.filter(m => m.id !== 'temp-user')
        return [
          ...filtered,
          {
            id: 'user-' + Date.now(),
            session_id: selectedSessionId,
            role: 'user',
            content: userMessage,
            created_at: new Date().toISOString(),
          },
          {
            id: response.data.chat_log_id,
            session_id: selectedSessionId,
            role: 'assistant',
            content: response.data.message,
            created_at: new Date().toISOString(),
          }
        ]
      })

      // Refresh sessions to update message counts and previews
      fetchSessions()
    } catch (error: any) {
      // Remove temp message on error
      setMessages(prev => prev.filter(m => m.id !== 'temp-user'))
      toast({
        title: "エラー",
        description: error.response?.data?.detail || "メッセージの送信に失敗しました",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider)
    const setting = llmSettings.find(s => s.provider === provider)
    if (setting) {
      setSelectedModel(setting.model)
    }
  }

  if (llmSettings.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-gray-500 mb-4">
            チャットを開始するには、まずLLM設定を追加してください
          </p>
          <p className="text-sm text-gray-400">
            設定タブからAPIキーとモデルを設定できます
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="flex h-[calc(100vh-200px)] gap-4">
      {/* Toggle Button for Mobile/Collapsed State */}
      {sidebarCollapsed && (
        <Button
          variant="outline"
          size="sm"
          onClick={() => setSidebarCollapsed(false)}
          className="fixed top-20 left-4 z-10 md:hidden"
        >
          <Menu className="h-4 w-4" />
        </Button>
      )}
      
      {/* Combined Sidebar */}
      {!sidebarCollapsed && (
        <Card className="w-80 flex flex-col transition-all duration-300">
        <CardHeader className="pb-3">
          <div className="flex justify-between items-center">
            <CardTitle className="text-lg">ナビゲーション</CardTitle>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarCollapsed(true)}
              className="h-8 w-8 p-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-4">
          {/* Project Info */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-2">プロジェクト</h3>
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <FolderOpen className="h-4 w-4 text-gray-600" />
                <span className="text-sm font-medium truncate">
                  {project?.title || 'プロジェクト'}
                </span>
              </div>
              {project?.description && (
                <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                  {project.description}
                </p>
              )}
            </div>
          </div>

          {/* Chat Sessions */}
          <div>
            <div className="flex justify-between items-center mb-3">
              <h3 className="text-sm font-medium text-gray-700">会話履歴</h3>
              <Button size="sm" onClick={createNewSession}>
                <Plus className="h-4 w-4 mr-2" />
                新規
              </Button>
            </div>
            <div className="space-y-2">
              {sessionsLoading ? (
                <div className="text-center py-4">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary mx-auto"></div>
                </div>
              ) : sessions.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">会話がありません</p>
                </div>
              ) : (
                sessions.map((session) => (
                  <div
                    key={session.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedSessionId === session.id
                        ? 'bg-primary text-primary-foreground'
                        : 'bg-gray-50 hover:bg-gray-100'
                    }`}
                    onClick={() => setSelectedSessionId(session.id)}
                  >
                    <div className="flex justify-between items-start mb-1">
                      {editingSessionId === session.id ? (
                        <Input
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onBlur={() => updateSessionTitle(session.id, editingTitle)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') {
                              updateSessionTitle(session.id, editingTitle)
                            } else if (e.key === 'Escape') {
                              setEditingSessionId(null)
                              setEditingTitle('')
                            }
                          }}
                          className="text-sm h-6 p-1"
                          autoFocus
                        />
                      ) : (
                        <h4 className="font-medium text-sm truncate flex-1">{session.title}</h4>
                      )}
                      <div className="flex gap-1 ml-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                          onClick={(e) => {
                            e.stopPropagation()
                            setEditingSessionId(session.id)
                            setEditingTitle(session.title)
                          }}
                        >
                          <Edit2 className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0"
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteSession(session.id)
                          }}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                    <div className="text-xs opacity-70">
                      {session.message_count} メッセージ
                    </div>
                    {session.last_message_preview && (
                      <div className="text-xs opacity-60 mt-1 line-clamp-2">
                        {session.last_message_preview}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </CardContent>
        </Card>
      )}

      {/* Chat Interface */}
      <Card className="flex-1 flex flex-col">
        {selectedSessionId ? (
          <>
            {/* Chat Header */}
            <CardHeader className="pb-3">
              <div className="flex justify-between items-center">
                <div className="flex items-center space-x-2">
                  {sidebarCollapsed && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSidebarCollapsed(false)}
                      className="h-8 w-8 p-0"
                    >
                      <Menu className="h-4 w-4" />
                    </Button>
                  )}
                  <CardTitle className="text-lg">
                    {sessions.find(s => s.id === selectedSessionId)?.title || 'チャット'}
                  </CardTitle>
                </div>
                <div className="flex items-center space-x-2">
                  <label className="text-sm font-medium">プロバイダー:</label>
                  <select
                    className="px-2 py-1 border border-gray-300 rounded text-sm"
                    value={selectedProvider}
                    onChange={(e) => handleProviderChange(e.target.value)}
                  >
                    {llmSettings.map(setting => (
                      <option key={setting.provider} value={setting.provider}>
                        {setting.provider} ({setting.model})
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </CardHeader>

            {/* Messages */}
            <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  メッセージを送信してチャットを開始してください
                </div>
              ) : (
                messages.map((message, index) => (
                  <div key={message.id || index} className="mb-6">
                    {message.role === 'user' ? (
                      <div className="flex justify-end">
                        <div className="max-w-[70%] p-3 rounded-lg bg-primary text-primary-foreground">
                          <div className="flex items-center space-x-2 mb-1">
                            <User className="h-4 w-4" />
                            <span className="text-xs opacity-70">あなた</span>
                          </div>
                          <div className="whitespace-pre-wrap">{message.content}</div>
                        </div>
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-center space-x-2 mb-3">
                          <Bot className="h-5 w-5 text-blue-600" />
                          <span className="text-sm font-medium text-gray-700">AI アシスタント</span>
                        </div>
                        <div className="w-full prose prose-sm max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeHighlight]}
                            components={{
                              code: ({ node, inline, className, children, ...props }) => {
                                const match = /language-(\w+)/.exec(className || '')
                                return !inline && match ? (
                                  <pre className="bg-gray-900 text-gray-100 rounded p-3 overflow-x-auto">
                                    <code className={className} {...props}>
                                      {children}
                                    </code>
                                  </pre>
                                ) : (
                                  <code className="bg-gray-100 px-1 py-0.5 rounded text-sm" {...props}>
                                    {children}
                                  </code>
                                )
                              },
                              pre: ({ children }) => <div>{children}</div>,
                              blockquote: ({ children }) => (
                                <blockquote className="border-l-4 border-blue-500 pl-4 italic">
                                  {children}
                                </blockquote>
                              ),
                              table: ({ children }) => (
                                <div className="overflow-x-auto">
                                  <table className="min-w-full border-collapse border border-gray-300">
                                    {children}
                                  </table>
                                </div>
                              ),
                              th: ({ children }) => (
                                <th className="border border-gray-300 px-3 py-2 bg-gray-100 font-medium">
                                  {children}
                                </th>
                              ),
                              td: ({ children }) => (
                                <td className="border border-gray-300 px-3 py-2">
                                  {children}
                                </td>
                              ),
                            }}
                          >
                            {message.content}
                          </ReactMarkdown>
                        </div>
                      </div>
                    )}
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </CardContent>

            {/* Message Input */}
            <div className="border-t p-4">
              <form onSubmit={handleSendMessage} className="flex space-x-2">
                <Input
                  placeholder="メッセージを入力..."
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  disabled={loading}
                  className="flex-1"
                />
                <Button type="submit" disabled={loading || !newMessage.trim()}>
                  {loading ? (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </form>
            </div>
          </>
        ) : (
          <CardContent className="flex-1 flex items-center justify-center">
            <div className="text-center text-gray-500">
              {sidebarCollapsed && (
                <Button
                  variant="outline"
                  onClick={() => setSidebarCollapsed(false)}
                  className="mb-4"
                >
                  <Menu className="h-4 w-4 mr-2" />
                  サイドバーを開く
                </Button>
              )}
              <MessageSquare className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>会話を選択してください</p>
              <p className="text-sm mt-2">または新しい会話を作成してください</p>
            </div>
          </CardContent>
        )}
      </Card>
    </div>
  )
}