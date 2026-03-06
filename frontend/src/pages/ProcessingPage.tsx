import { useCallback, useMemo } from 'react'
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
  AlertTriangle,
} from 'lucide-react'
import { api } from '@/api/client'

const phases = [
  { key: 'quality', label: 'Quality', icon: Search },
  { key: 'clustering', label: 'Clustering', icon: Layers },
  { key: 'best_picks', label: 'Best Picks', icon: Star },
]

const categoryColors: Record<string, { dot: string; text: string; bg: string }> = {
  good:         { dot: 'bg-good',         text: 'text-good',         bg: 'bg-good/10' },
  blurry:       { dot: 'bg-blurry',       text: 'text-blurry',       bg: 'bg-blurry/10' },
  overexposed:  { dot: 'bg-overexposed',  text: 'text-overexposed',  bg: 'bg-overexposed/10' },
  underexposed: { dot: 'bg-underexposed', text: 'text-underexposed', bg: 'bg-underexposed/10' },
}

export function ProcessingPage() {
  const navigate = useNavigate()
  const {
    currentSession, isProcessing, progress, phaseStats,
    handleProgressEvent, setProcessing, loadResults, processedImages, warnings,
  } = useSessionStore()

  const onEvent = useCallback(
    (event: any) => {
      handleProgressEvent(event)
      if (event.type === 'pipeline_complete' && currentSession) {
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

  // Live stat counters from processedImages
  const liveCounts = useMemo(() => {
    const counts = { good: 0, blurry: 0, overexposed: 0, underexposed: 0 }
    for (const img of processedImages) {
      if (img.category in counts) {
        counts[img.category as keyof typeof counts]++
      }
    }
    return counts
  }, [processedImages])

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
  const isQualityPhase = currentPhase === 'quality'
  const isClusterPhase = currentPhase === 'clustering'
  const pct = progress && progress.total > 0
    ? Math.round((progress.current / progress.total) * 100)
    : 0

  return (
    <PageContainer
      title="Processing"
      subtitle={
        isProcessing
          ? `Analyzing ${currentSession.image_count} images...`
          : 'Processing complete'
      }
    >
      {/* Compact phase indicators */}
      <div className="flex items-center justify-center gap-2 mb-6">
        {phases.map((phase, i) => {
          const isComplete = phaseStats[phase.key] != null
          const isCurrent = phase.key === currentPhase
          const Icon = phase.icon
          return (
            <div key={phase.key} className="flex items-center">
              {i > 0 && (
                <div className={cn('w-8 h-px mx-1', isComplete || isCurrent ? 'bg-accent' : 'bg-border')} />
              )}
              <div
                className={cn(
                  'w-9 h-9 rounded-full flex items-center justify-center border-2 transition-all',
                  isComplete && 'border-accent bg-accent/10 text-accent',
                  isCurrent && 'border-accent bg-accent text-background',
                  !isComplete && !isCurrent && 'border-border text-text-muted',
                )}
                title={phase.label}
              >
                {isComplete ? <Check className="w-4 h-4" /> : isCurrent ? <Loader2 className="w-4 h-4 animate-spin" /> : <Icon className="w-4 h-4" />}
              </div>
            </div>
          )
        })}
      </div>

      {/* Warning banners */}
      {warnings.length > 0 && (
        <div className="max-w-2xl mx-auto mb-4 space-y-2">
          {warnings.map((msg, i) => (
            <div key={i} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 text-sm">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{msg}</span>
            </div>
          ))}
        </div>
      )}

      {/* Progress bar */}
      {isProcessing && progress && progress.total > 0 && (
        <div className="max-w-2xl mx-auto mb-6">
          <div className="flex items-center justify-between text-xs text-text-muted mb-1.5">
            <span>
              {isClusterPhase
                ? (progress.step || 'Processing...')
                : `${progress.current} / ${progress.total} images`}
            </span>
            <span className="text-accent font-mono font-medium">{pct}%</span>
          </div>
          <div className="h-1.5 bg-surface-active rounded-full overflow-hidden">
            <div
              className="h-full bg-accent rounded-full transition-all duration-200"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>
      )}

      {/* Live stat counters */}
      {processedImages.length > 0 && (
        <div className="flex items-center justify-center gap-4 mb-6">
          {(['good', 'blurry', 'overexposed', 'underexposed'] as const).map((cat) => {
            const colors = categoryColors[cat]
            const count = liveCounts[cat]
            return (
              <div
                key={cat}
                className={cn(
                  'flex items-center gap-2 px-3 py-1.5 rounded-lg transition-all',
                  count > 0 ? colors.bg : 'bg-surface',
                )}
              >
                <span className={cn('w-2 h-2 rounded-full', colors.dot)} />
                <span className={cn('text-lg font-bold tabular-nums', count > 0 ? colors.text : 'text-text-muted')}>
                  {count}
                </span>
                <span className="text-xs text-text-muted capitalize">{cat}</span>
              </div>
            )
          })}
        </div>
      )}

      {/* Clustering phase: special visualization */}
      {isClusterPhase && (
        <div className="max-w-md mx-auto text-center py-8">
          <div className="relative w-20 h-20 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-2 border-accent/30 animate-ping" />
            <div className="absolute inset-2 rounded-full border-2 border-accent/50 animate-ping [animation-delay:0.5s]" />
            <div className="absolute inset-0 rounded-full border-2 border-accent flex items-center justify-center">
              <Layers className="w-8 h-8 text-accent" />
            </div>
          </div>
          <p className="text-text-secondary text-sm">
            {progress?.step === 'loading_model' && 'Loading AI model...'}
            {progress?.step === 'computing_hashes' && 'Computing perceptual hashes...'}
            {progress?.step === 'extracting_embeddings' && 'Extracting visual embeddings...'}
            {progress?.step === 'clustering' && 'Grouping similar images...'}
            {progress?.step === 'organizing_files' && 'Organizing files into groups...'}
            {!progress?.step && 'Analyzing similarity...'}
          </p>
        </div>
      )}

      {/* LIVE IMAGE MOSAIC */}
      {processedImages.length > 0 && (isQualityPhase || phaseStats.quality) && (
        <div className="mt-4">
          <div className="grid gap-1" style={{
            gridTemplateColumns: 'repeat(auto-fill, minmax(72px, 1fr))',
          }}>
            {processedImages.map((img) => {
              const colors = categoryColors[img.category] || categoryColors.good
              return (
                <div
                  key={img.filename}
                  className="relative aspect-square rounded-md overflow-hidden bg-surface-hover group"
                >
                  <img
                    src={api.imageUrl(currentSession.id, img.filename, 'thumb')}
                    alt={img.filename}
                    className="w-full h-full object-cover"
                    loading="lazy"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none'
                    }}
                  />
                  {/* Category dot */}
                  <div className={cn('absolute top-1 right-1 w-2.5 h-2.5 rounded-full border border-black/30', colors.dot)} />
                  {/* Score overlay on hover */}
                  <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                    <span className="text-xs font-bold text-white">{img.score}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Phase completion stats (shown when done) */}
      {Object.keys(phaseStats).length > 0 && !isProcessing && (
        <div className="max-w-xl mx-auto mt-8 space-y-2">
          {phaseStats.quality && (
            <div className="flex items-center gap-2 text-sm">
              <Check className="w-4 h-4 text-accent" />
              <span className="text-good">{phaseStats.quality.good} good</span>
              <span className="text-text-muted">&middot;</span>
              <span className="text-blurry">{phaseStats.quality.blurry} blurry</span>
              <span className="text-text-muted">&middot;</span>
              <span className="text-overexposed">{phaseStats.quality.overexposed} over</span>
              <span className="text-text-muted">&middot;</span>
              <span className="text-underexposed">{phaseStats.quality.underexposed} under</span>
            </div>
          )}
          {phaseStats.clustering && (
            <div className="flex items-center gap-2 text-sm">
              <Check className="w-4 h-4 text-accent" />
              <span>{phaseStats.clustering.clusters} groups, {phaseStats.clustering.unique} unique</span>
            </div>
          )}
          {phaseStats.best_picks && (
            <div className="flex items-center gap-2 text-sm">
              <Check className="w-4 h-4 text-accent" />
              <span>{phaseStats.best_picks.count} best picks selected</span>
            </div>
          )}
        </div>
      )}

      {/* Cancel button */}
      {isProcessing && (
        <div className="max-w-xs mx-auto mt-8">
          <button
            onClick={handleCancel}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg border border-border text-sm text-text-muted hover:text-overexposed hover:border-overexposed/50 transition-colors"
          >
            <StopCircle className="w-4 h-4" />
            Cancel
          </button>
        </div>
      )}
    </PageContainer>
  )
}
