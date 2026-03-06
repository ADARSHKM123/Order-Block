import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageContainer } from '@/components/layout/PageContainer'
import { useSessionStore } from '@/stores/session-store'
import { useWebSocket } from '@/hooks/useWebSocket'
import { cn } from '@/lib/utils'
import {
  Search,
  Layers,
  Star,
  Check,
  Loader2,
  StopCircle,
} from 'lucide-react'
import { api } from '@/api/client'

const phases = [
  { key: 'quality', label: 'Quality Analysis', icon: Search, description: 'Analyzing sharpness, exposure, and noise' },
  { key: 'clustering', label: 'Similarity Clustering', icon: Layers, description: 'Grouping similar images together' },
  { key: 'best_picks', label: 'Best Pick Selection', icon: Star, description: 'Selecting the best image from each group' },
]

export function ProcessingPage() {
  const navigate = useNavigate()
  const { currentSession, isProcessing, progress, phaseStats, handleProgressEvent, setProcessing, loadResults } = useSessionStore()

  const onEvent = useCallback(
    (event: any) => {
      handleProgressEvent(event)
      if (event.type === 'pipeline_complete' && currentSession) {
        // Load results and navigate
        loadResults(currentSession.id).then(() => navigate('/results'))
      }
    },
    [handleProgressEvent, currentSession, loadResults, navigate],
  )

  useWebSocket(currentSession?.id || null, onEvent, isProcessing)

  const handleCancel = async () => {
    if (currentSession) {
      await api.cancelProcessing(currentSession.id)
      setProcessing(false)
    }
  }

  if (!currentSession) {
    return (
      <PageContainer title="Processing" subtitle="No active session">
        <div className="text-center py-20">
          <p className="text-text-muted mb-4">Start from the Dashboard.</p>
          <button onClick={() => navigate('/')} className="px-4 py-2 bg-accent text-background rounded-lg font-medium">
            Go to Dashboard
          </button>
        </div>
      </PageContainer>
    )
  }

  const currentPhase = progress?.phase || ''

  return (
    <PageContainer
      title="Processing"
      subtitle={isProcessing ? 'Analyzing your images...' : 'Processing complete'}
    >
      {/* Phase indicators */}
      <div className="flex items-center justify-center gap-0 mb-12">
        {phases.map((phase, i) => {
          const isComplete = phaseStats[phase.key] != null
          const isCurrent = phase.key === currentPhase
          const isPending = !isComplete && !isCurrent
          const Icon = phase.icon

          return (
            <div key={phase.key} className="flex items-center">
              {i > 0 && (
                <div
                  className={cn(
                    'w-16 h-0.5 transition-colors',
                    isComplete || isCurrent ? 'bg-accent' : 'bg-border',
                  )}
                />
              )}
              <div className="flex flex-col items-center gap-2">
                <div
                  className={cn(
                    'w-14 h-14 rounded-full flex items-center justify-center border-2 transition-all',
                    isComplete && 'border-accent bg-accent/10 text-accent',
                    isCurrent && 'border-accent bg-accent text-background animate-pulse',
                    isPending && 'border-border text-text-muted',
                  )}
                >
                  {isComplete ? (
                    <Check className="w-6 h-6" />
                  ) : isCurrent ? (
                    <Loader2 className="w-6 h-6 animate-spin" />
                  ) : (
                    <Icon className="w-6 h-6" />
                  )}
                </div>
                <div className="text-center">
                  <p
                    className={cn(
                      'text-sm font-medium',
                      isCurrent && 'text-accent',
                      isComplete && 'text-text-primary',
                      isPending && 'text-text-muted',
                    )}
                  >
                    {phase.label}
                  </p>
                  <p className="text-xs text-text-muted">{phase.description}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Progress details */}
      {progress && isProcessing && (
        <div className="max-w-xl mx-auto">
          <div className="border border-border rounded-xl bg-surface p-6 mb-6">
            {/* Progress bar */}
            {progress.total > 0 && (
              <div className="mb-4">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-text-secondary">
                    {progress.step || `${progress.current} / ${progress.total}`}
                  </span>
                  <span className="text-accent font-mono">
                    {Math.round((progress.current / progress.total) * 100)}%
                  </span>
                </div>
                <div className="h-2 bg-surface-active rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent rounded-full transition-all duration-300"
                    style={{ width: `${(progress.current / progress.total) * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Current image */}
            {progress.image && (
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-lg bg-surface-hover overflow-hidden">
                  <img
                    src={api.imageUrl(currentSession.id, progress.image, 'thumb')}
                    alt=""
                    className="w-full h-full object-cover"
                    onError={(e) => (e.currentTarget.style.display = 'none')}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm truncate">{progress.image}</p>
                  {progress.category && (
                    <span
                      className={cn(
                        'text-xs px-2 py-0.5 rounded-full mt-1 inline-block',
                        progress.category === 'good' && 'bg-good/10 text-good',
                        progress.category === 'blurry' && 'bg-blurry/10 text-blurry',
                        progress.category === 'overexposed' && 'bg-overexposed/10 text-overexposed',
                        progress.category === 'underexposed' && 'bg-underexposed/10 text-underexposed',
                      )}
                    >
                      {progress.category}
                      {progress.score != null && ` · ${progress.score}`}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Cancel button */}
          <button
            onClick={handleCancel}
            className="w-full flex items-center justify-center gap-2 px-4 py-3 rounded-xl border border-border text-text-secondary hover:text-overexposed hover:border-overexposed/50 transition-colors"
          >
            <StopCircle className="w-4 h-4" />
            Cancel Processing
          </button>
        </div>
      )}

      {/* Phase stats */}
      {Object.keys(phaseStats).length > 0 && (
        <div className="max-w-xl mx-auto mt-6 space-y-3">
          {phaseStats.quality && (
            <div className="flex items-center gap-3 text-sm">
              <Check className="w-4 h-4 text-accent" />
              <span>
                Quality:{' '}
                <span className="text-good">{phaseStats.quality.good} good</span>,{' '}
                <span className="text-blurry">{phaseStats.quality.blurry} blurry</span>,{' '}
                <span className="text-overexposed">{phaseStats.quality.overexposed} overexposed</span>,{' '}
                <span className="text-underexposed">{phaseStats.quality.underexposed} underexposed</span>
              </span>
            </div>
          )}
          {phaseStats.clustering && (
            <div className="flex items-center gap-3 text-sm">
              <Check className="w-4 h-4 text-accent" />
              <span>
                Clustering: {phaseStats.clustering.clusters} groups, {phaseStats.clustering.unique} unique
              </span>
            </div>
          )}
          {phaseStats.best_picks && (
            <div className="flex items-center gap-3 text-sm">
              <Check className="w-4 h-4 text-accent" />
              <span>Best picks: {phaseStats.best_picks.count} selected</span>
            </div>
          )}
        </div>
      )}
    </PageContainer>
  )
}
