'use client'

import { useState, useEffect, useRef } from 'react'
import { chatApi, llmSettingsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useToast } from '@/components/ui/use-toast'
import { Send, Trash2, Bot, User } from 'lucide-react'

interface ChatLog {
  id: string
  role: string
  content: string
  created_at: string
}

interface LLMSetting {
  provider: string
  model: string
}

interface ChatInterfaceProps {
  projectId: string
}

export function ChatInterface({ projectId }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatLog[]>([])
  const [newMessage, setNewMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const [historyLoading, setHistoryLoading] = useState(true)
  const [llmSettings, setLlmSettings] = useState<LLMSetting[]>([])
  const [selectedProvider, setSelectedProvider] = useState<string>('')
  const [selectedModel, setSelectedModel] = useState<string>('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const { toast } = useToast()

  useEffect(() => {
    fetchChatHistory()
    fetchLLMSettings()
  }, [projectId])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const fetchChatHistory = async () => {
    try {
      const response = await chatApi.getHistory(projectId)
      setMessages(response.data)
    } catch (error) {
      toast({
        title: "エラー",
        description: "チャット履歴の取得に失敗しました",
        variant: "destructive",
      })
    } finally {
      setHistoryLoading(false)
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

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newMessage.trim() || !selectedProvider) return

    const userMessage = newMessage.trim()
    setNewMessage('')
    setLoading(true)

    // Add user message to UI immediately
    const tempUserMessage: ChatLog = {
      id: 'temp-user',
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
    }
    setMessages(prev => [...prev, tempUserMessage])

    try {
      const response = await chatApi.send({
        message: userMessage,
        project_id: projectId,
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
            role: 'user',
            content: userMessage,
            created_at: new Date().toISOString(),
          },
          {
            id: response.data.chat_log_id,
            role: 'assistant',
            content: response.data.message,
            created_at: new Date().toISOString(),
          }
        ]
      })
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

  const handleClearHistory = async () => {
    if (!confirm('チャット履歴を削除しますか？')) return

    try {
      await chatApi.clearHistory(projectId)
      setMessages([])
      toast({
        title: "履歴削除成功",
        description: "チャット履歴が削除されました",
      })
    } catch (error) {
      toast({
        title: "エラー",
        description: "履歴の削除に失敗しました",
        variant: "destructive",
      })
    }
  }

  const handleProviderChange = (provider: string) => {
    setSelectedProvider(provider)
    const setting = llmSettings.find(s => s.provider === provider)
    if (setting) {
      setSelectedModel(setting.model)
    }
  }

  if (historyLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
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
    <div className="flex flex-col h-[calc(100vh-200px)]">
      {/* Chat Header */}
      <Card className="mb-4">
        <CardHeader className="pb-3">
          <div className="flex justify-between items-center">
            <CardTitle className="text-lg">チャット</CardTitle>
            <div className="flex items-center space-x-4">
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
              <Button variant="outline" size="sm" onClick={handleClearHistory}>
                <Trash2 className="h-4 w-4 mr-2" />
                履歴削除
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Messages */}
      <Card className="flex-1 flex flex-col">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              メッセージを送信してチャットを開始してください
            </div>
          ) : (
            messages.map((message, index) => (
              <div
                key={message.id || index}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] p-3 rounded-lg ${
                    message.role === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    {message.role === 'user' ? (
                      <User className="h-4 w-4" />
                    ) : (
                      <Bot className="h-4 w-4" />
                    )}
                    <span className="text-xs opacity-70">
                      {message.role === 'user' ? 'あなた' : 'AI'}
                    </span>
                  </div>
                  <div className="whitespace-pre-wrap">{message.content}</div>
                </div>
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
      </Card>
    </div>
  )
}