'use client'

import { useState, useEffect } from 'react'
import { projectsApi } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { useToast } from '@/components/ui/use-toast'
import { Plus, Trash2, Edit } from 'lucide-react'

interface Project {
  id: string
  title: string
  description?: string
  created_at: string
}

interface ProjectListProps {
  onProjectSelect: (projectId: string) => void
}

export function ProjectList({ onProjectSelect }: ProjectListProps) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [newProject, setNewProject] = useState({ title: '', description: '' })
  const { toast } = useToast()

  useEffect(() => {
    fetchProjects()
  }, [])

  const fetchProjects = async () => {
    try {
      const response = await projectsApi.getAll()
      setProjects(response.data)
    } catch (error) {
      toast({
        title: "エラー",
        description: "プロジェクトの取得に失敗しました",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProject.title.trim()) return

    try {
      const response = await projectsApi.create(newProject)
      setProjects([response.data, ...projects])
      setNewProject({ title: '', description: '' })
      setCreating(false)
      toast({
        title: "プロジェクト作成成功",
        description: "新しいプロジェクトが作成されました",
      })
    } catch (error) {
      toast({
        title: "エラー",
        description: "プロジェクトの作成に失敗しました",
        variant: "destructive",
      })
    }
  }

  const handleDeleteProject = async (projectId: string) => {
    if (!confirm('このプロジェクトを削除しますか？')) return

    try {
      await projectsApi.delete(projectId)
      setProjects(projects.filter(p => p.id !== projectId))
      toast({
        title: "プロジェクト削除成功",
        description: "プロジェクトが削除されました",
      })
    } catch (error) {
      toast({
        title: "エラー",
        description: "プロジェクトの削除に失敗しました",
        variant: "destructive",
      })
    }
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
        <h2 className="text-2xl font-bold text-gray-900">プロジェクト一覧</h2>
        <Button onClick={() => setCreating(true)}>
          <Plus className="h-4 w-4 mr-2" />
          新規プロジェクト
        </Button>
      </div>

      {creating && (
        <Card>
          <CardHeader>
            <CardTitle>新規プロジェクト作成</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateProject} className="space-y-4">
              <div>
                <Input
                  placeholder="プロジェクト名"
                  value={newProject.title}
                  onChange={(e) => setNewProject({ ...newProject, title: e.target.value })}
                  required
                />
              </div>
              <div>
                <Input
                  placeholder="説明（任意）"
                  value={newProject.description}
                  onChange={(e) => setNewProject({ ...newProject, description: e.target.value })}
                />
              </div>
              <div className="flex space-x-2">
                <Button type="submit">作成</Button>
                <Button type="button" variant="outline" onClick={() => setCreating(false)}>
                  キャンセル
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {projects.map((project) => (
          <Card key={project.id} className="cursor-pointer hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div onClick={() => onProjectSelect(project.id)} className="flex-1">
                  <CardTitle className="text-lg">{project.title}</CardTitle>
                  {project.description && (
                    <CardDescription className="mt-2">
                      {project.description}
                    </CardDescription>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation()
                    handleDeleteProject(project.id)
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500">
                作成日: {new Date(project.created_at).toLocaleDateString('ja-JP')}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {projects.length === 0 && !creating && (
        <div className="text-center py-12">
          <p className="text-gray-500 mb-4">プロジェクトがありません</p>
          <Button onClick={() => setCreating(true)}>
            <Plus className="h-4 w-4 mr-2" />
            最初のプロジェクトを作成
          </Button>
        </div>
      )}
    </div>
  )
}