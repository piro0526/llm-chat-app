'use client'

import { useState, useEffect } from 'react'
import { llmSettingsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/use-toast'
import { Plus, Trash2, Eye, EyeOff } from 'lucide-react'

interface LLMSetting {
  provider: string
  model: string
}

const PROVIDERS = [
  { id: 'openai', name: 'OpenAI', models: ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'] },
  { id: 'claude', name: 'Claude', models: ['claude-3-sonnet-20240229', 'claude-3-opus-20240229', 'claude-3-haiku-20240307'] },
  { id: 'gemini', name: 'Gemini', models: ['gemini-pro', 'gemini-pro-vision'] },
]

export function LLMSettings() {
  const [settings, setSettings] = useState<LLMSetting[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [showApiKey, setShowApiKey] = useState<Record<string, boolean>>({})
  const [newSetting, setNewSetting] = useState({
    provider: '',
    api_key: '',
    model: '',
  })
  const { toast } = useToast()

  useEffect(() => {
    fetchSettings()
  }, [])

  const fetchSettings = async () => {
    try {
      const response = await llmSettingsApi.getAll()
      setSettings(response.data)
    } catch (error) {
      toast({
        title: "エラー",
        description: "設定の取得に失敗しました",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateSetting = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newSetting.provider || !newSetting.api_key || !newSetting.model) return

    try {
      const response = await llmSettingsApi.create(newSetting)
      setSettings([...settings, response.data])
      setNewSetting({ provider: '', api_key: '', model: '' })
      setCreating(false)
      toast({
        title: "設定追加成功",
        description: "LLM設定が追加されました",
      })
    } catch (error: any) {
      toast({
        title: "エラー",
        description: error.response?.data?.detail || "設定の追加に失敗しました",
        variant: "destructive",
      })
    }
  }

  const handleDeleteSetting = async (provider: string) => {
    if (!confirm('この設定を削除しますか？')) return

    try {
      await llmSettingsApi.delete(provider)
      setSettings(settings.filter(s => s.provider !== provider))
      toast({
        title: "設定削除成功",
        description: "LLM設定が削除されました",
      })
    } catch (error) {
      toast({
        title: "エラー",
        description: "設定の削除に失敗しました",
        variant: "destructive",
      })
    }
  }

  const getProviderName = (provider: string) => {
    return PROVIDERS.find(p => p.id === provider)?.name || provider
  }

  const getProviderModels = (provider: string) => {
    return PROVIDERS.find(p => p.id === provider)?.models || []
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">LLM設定</h2>
        <Button onClick={() => setCreating(true)}>
          <Plus className="h-4 w-4 mr-2" />
          設定追加
        </Button>
      </div>

      {creating && (
        <Card>
          <CardHeader>
            <CardTitle>新規LLM設定</CardTitle>
            <CardDescription>
              LLMプロバイダーのAPIキーとモデルを設定してください
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateSetting} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">プロバイダー</label>
                <select
                  className="w-full p-2 border border-input bg-background rounded-md text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  value={newSetting.provider}
                  onChange={(e) => setNewSetting({ 
                    ...newSetting, 
                    provider: e.target.value,
                    model: '' // Reset model when provider changes
                  })}
                  required
                >
                  <option value="">選択してください</option>
                  {PROVIDERS.filter(p => !settings.find(s => s.provider === p.id)).map(provider => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">APIキー</label>
                <Input
                  type="password"
                  placeholder="APIキーを入力"
                  value={newSetting.api_key}
                  onChange={(e) => setNewSetting({ ...newSetting, api_key: e.target.value })}
                  required
                />
              </div>
              {newSetting.provider && (
                <div>
                  <label className="block text-sm font-medium mb-2">モデル</label>
                  <select
                    className="w-full p-2 border border-input bg-background rounded-md text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                    value={newSetting.model}
                    onChange={(e) => setNewSetting({ ...newSetting, model: e.target.value })}
                    required
                  >
                    <option value="">選択してください</option>
                    {getProviderModels(newSetting.provider).map(model => (
                      <option key={model} value={model}>
                        {model}
                      </option>
                    ))}
                  </select>
                </div>
              )}
              <div className="flex space-x-2">
                <Button type="submit">追加</Button>
                <Button type="button" variant="outline" onClick={() => setCreating(false)}>
                  キャンセル
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {settings.map((setting) => (
          <Card key={setting.provider}>
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-lg">
                    {getProviderName(setting.provider)}
                  </CardTitle>
                  <CardDescription className="mt-2">
                    モデル: {setting.model}
                  </CardDescription>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteSetting(setting.provider)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-500">APIキー設定済み</span>
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {settings.length === 0 && !creating && (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">LLM設定がありません</p>
          <Button onClick={() => setCreating(true)}>
            <Plus className="h-4 w-4 mr-2" />
            最初の設定を追加
          </Button>
        </div>
      )}
    </div>
  )
}