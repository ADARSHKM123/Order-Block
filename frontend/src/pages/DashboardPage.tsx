import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageContainer } from '@/components/layout/PageContainer'
import { FolderBrowser } from '@/components/folder-picker/FolderBrowser'
import { useSessionStore } from '@/stores/session-store'
import { cn } from '@/lib/utils'
import {
  ArrowRight,
  Clock,
  Trash2,
  Images,
  CheckCircle2,
  XCircle,
  Loader2,
} from 'lucide-react'

export function DashboardPage() {
  const navigate = useNavigate()
  const { sessions, loadSessions, createSession, setCurrentSession, deleteSession } = useSessionStore()
  const [inputPath, setInputPath] = useState('')
  const [outputPath, setOutputPath] = useState('')
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  const handleCreate = async () => {
    if (!inputPath || !outputPath) {
      setError('Please select both input and output folders')
      return
    }
    setCreating(true)
    setError('')
    try {
      await createSession(inputPath, outputPath)
      navigate('/settings')
    } catch (e: any) {
      setError(e.message)
    } finally {
      setCreating(false)
    }
  }

  const handleResumeSession = async (session: typeof sessions[0]) => {
    setCurrentSession(session)
    if (session.status === 'complete') {
      navigate('/results')
    } else if (session.status === 'processing') {
      navigate('/processing')
    } else {
      navigate('/settings')
    }
  }

  const statusConfig = {
    pending: { icon: Clock, color: 'text-text-muted', bg: 'bg-surface-hover' },
    processing: { icon: Loader2, color: 'text-accent', bg: 'bg-accent/10' },
    complete: { icon: CheckCircle2, color: 'text-good', bg: 'bg-good/10' },
    error: { icon: XCircle, color: 'text-overexposed', bg: 'bg-overexposed/10' },
    cancelled: { icon: XCircle, color: 'text-text-muted', bg: 'bg-surface-hover' },
  }

  return (
    <PageContainer
      title="Dashboard"
      subtitle="Select a folder to sort your images"
    >
      {/* New Session */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
        <FolderBrowser
          label="Input Folder — where your photos are"
          onSelect={setInputPath}
          selectedPath={inputPath}
        />
        <FolderBrowser
          label="Output Folder — where sorted photos will go"
          onSelect={setOutputPath}
          selectedPath={outputPath}
        />
      </div>

      {error && (
        <div className="mb-4 px-4 py-3 rounded-lg bg-overexposed/10 text-overexposed text-sm">
          {error}
        </div>
      )}

      <button
        onClick={handleCreate}
        disabled={creating || !inputPath || !outputPath}
        className={cn(
          'w-full flex items-center justify-center gap-2 px-6 py-4 rounded-xl text-base font-semibold transition-all',
          inputPath && outputPath
            ? 'bg-accent text-background hover:bg-accent-hover shadow-lg shadow-accent/20'
            : 'bg-surface-hover text-text-muted cursor-not-allowed',
        )}
      >
        {creating ? (
          <Loader2 className="w-5 h-5 animate-spin" />
        ) : (
          <>
            Continue to Settings
            <ArrowRight className="w-5 h-5" />
          </>
        )}
      </button>

      {/* Recent Sessions */}
      {sessions.length > 0 && (
        <div className="mt-12">
          <h2 className="text-lg font-semibold mb-4">Recent Sessions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sessions.map((s) => {
              const cfg = statusConfig[s.status] || statusConfig.pending
              const StatusIcon = cfg.icon
              return (
                <div
                  key={s.id}
                  className="group border border-border rounded-xl bg-surface hover:border-border-hover transition-colors cursor-pointer"
                  onClick={() => handleResumeSession(s)}
                >
                  <div className="p-4">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate">{s.name}</p>
                        <p className="text-xs text-text-muted mt-0.5">
                          {new Date(s.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <span className={cn('flex items-center gap-1 text-xs px-2 py-1 rounded-full', cfg.bg, cfg.color)}>
                        <StatusIcon className="w-3 h-3" />
                        {s.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-text-muted">
                      <span className="flex items-center gap-1">
                        <Images className="w-3 h-3" />
                        {s.image_count} images
                      </span>
                      {s.summary && (
                        <span className="text-good">{s.summary.good} good</span>
                      )}
                    </div>
                  </div>
                  <div className="border-t border-border px-4 py-2 flex justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        deleteSession(s.id)
                      }}
                      className="text-text-muted hover:text-overexposed transition-colors p-1"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </PageContainer>
  )
}
