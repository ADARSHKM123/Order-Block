import { useNavigate } from 'react-router-dom'
import { PageContainer } from '@/components/layout/PageContainer'
import { useSettingsStore } from '@/stores/settings-store'
import { useSessionStore } from '@/stores/session-store'
import { cn } from '@/lib/utils'
import {
  Zap,
  Brain,
  Play,
  RotateCcw,
  Copy,
  Move,
} from 'lucide-react'

function Slider({
  label,
  value,
  min,
  max,
  step = 1,
  onChange,
  description,
}: {
  label: string
  value: number
  min: number
  max: number
  step?: number
  onChange: (v: number) => void
  description?: string
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium">{label}</label>
        <span className="text-sm text-accent font-mono">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-surface-active rounded-lg appearance-none cursor-pointer accent-accent"
      />
      {description && (
        <p className="text-xs text-text-muted mt-1.5">{description}</p>
      )}
    </div>
  )
}

export function SettingsPage() {
  const navigate = useNavigate()
  const { settings, updateSettings, resetSettings } = useSettingsStore()
  const { currentSession, startProcessing } = useSessionStore()

  const handleStart = async () => {
    if (!currentSession) return
    await startProcessing(currentSession.id, settings)
    navigate('/processing')
  }

  if (!currentSession) {
    return (
      <PageContainer title="Settings" subtitle="No session selected">
        <div className="text-center py-20">
          <p className="text-text-muted mb-4">Create a session first from the Dashboard.</p>
          <button
            onClick={() => navigate('/')}
            className="px-4 py-2 bg-accent text-background rounded-lg font-medium"
          >
            Go to Dashboard
          </button>
        </div>
      </PageContainer>
    )
  }

  return (
    <PageContainer
      title="Processing Settings"
      subtitle={`Configure how ${currentSession.image_count} images will be analyzed`}
      actions={
        <button
          onClick={resetSettings}
          className="flex items-center gap-1.5 px-3 py-2 text-sm text-text-secondary hover:text-text-primary rounded-lg hover:bg-surface-hover transition-colors"
        >
          <RotateCcw className="w-4 h-4" />
          Reset
        </button>
      }
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Quality Thresholds */}
        <div className="border border-border rounded-xl bg-surface p-6">
          <h3 className="font-semibold mb-1">Quality Thresholds</h3>
          <p className="text-sm text-text-muted mb-6">
            Adjust how strictly images are categorized
          </p>
          <div className="space-y-6">
            <Slider
              label="Blur Detection"
              value={settings.blur_threshold}
              min={30}
              max={300}
              step={10}
              onChange={(v) => updateSettings({ blur_threshold: v })}
              description="Lower = more strict (more images flagged as blurry)"
            />
            <Slider
              label="Overexposure"
              value={settings.overexposure_threshold}
              min={180}
              max={250}
              step={5}
              onChange={(v) => updateSettings({ overexposure_threshold: v })}
              description="Lower = more strict (more images flagged as overexposed)"
            />
            <Slider
              label="Underexposure"
              value={settings.underexposure_threshold}
              min={10}
              max={80}
              step={5}
              onChange={(v) => updateSettings({ underexposure_threshold: v })}
              description="Higher = more strict (more images flagged as underexposed)"
            />
          </div>
        </div>

        {/* Clustering */}
        <div className="border border-border rounded-xl bg-surface p-6">
          <h3 className="font-semibold mb-1">Similarity Clustering</h3>
          <p className="text-sm text-text-muted mb-6">
            Group similar images together and auto-select the best one
          </p>

          {/* Cluster toggle */}
          <div className="flex items-center justify-between mb-6">
            <span className="text-sm font-medium">Enable Clustering</span>
            <button
              onClick={() => updateSettings({ cluster: !settings.cluster })}
              className={cn(
                'w-11 h-6 rounded-full transition-colors relative',
                settings.cluster ? 'bg-accent' : 'bg-surface-active',
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 w-5 h-5 rounded-full bg-white transition-transform',
                  settings.cluster ? 'translate-x-5.5' : 'translate-x-0.5',
                )}
              />
            </button>
          </div>

          {settings.cluster && (
            <>
              {/* Mode selection */}
              <div className="grid grid-cols-2 gap-3 mb-6">
                <button
                  onClick={() => updateSettings({ fast: false })}
                  className={cn(
                    'flex flex-col items-center gap-2 p-4 rounded-xl border transition-colors',
                    !settings.fast
                      ? 'border-accent bg-accent/5 text-accent'
                      : 'border-border hover:border-border-hover',
                  )}
                >
                  <Brain className="w-6 h-6" />
                  <span className="text-sm font-medium">CLIP (Accurate)</span>
                  <span className="text-xs text-text-muted">AI-powered</span>
                </button>
                <button
                  onClick={() => updateSettings({ fast: true })}
                  className={cn(
                    'flex flex-col items-center gap-2 p-4 rounded-xl border transition-colors',
                    settings.fast
                      ? 'border-accent bg-accent/5 text-accent'
                      : 'border-border hover:border-border-hover',
                  )}
                >
                  <Zap className="w-6 h-6" />
                  <span className="text-sm font-medium">Fast (Hash)</span>
                  <span className="text-xs text-text-muted">Lightweight</span>
                </button>
              </div>

              <Slider
                label="Similarity Threshold"
                value={settings.fast ? settings.hash_threshold : settings.similarity_threshold}
                min={settings.fast ? 1 : 0.05}
                max={settings.fast ? 30 : 0.5}
                step={settings.fast ? 1 : 0.05}
                onChange={(v) =>
                  updateSettings(settings.fast ? { hash_threshold: v } : { similarity_threshold: v })
                }
                description={settings.fast ? 'Lower = stricter matching' : 'Lower = stricter matching'}
              />
            </>
          )}
        </div>

        {/* Performance */}
        <div className="border border-border rounded-xl bg-surface p-6">
          <h3 className="font-semibold mb-1">Performance</h3>
          <p className="text-sm text-text-muted mb-6">
            Parallel processing and file handling
          </p>
          <Slider
            label="Worker Threads"
            value={settings.workers}
            min={1}
            max={16}
            onChange={(v) => updateSettings({ workers: v })}
            description="More workers = faster processing but higher CPU usage"
          />
        </div>

        {/* File Handling */}
        <div className="border border-border rounded-xl bg-surface p-6">
          <h3 className="font-semibold mb-1">File Handling</h3>
          <p className="text-sm text-text-muted mb-6">
            How files are organized in the output folder
          </p>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => updateSettings({ move: false })}
              className={cn(
                'flex flex-col items-center gap-2 p-4 rounded-xl border transition-colors',
                !settings.move
                  ? 'border-accent bg-accent/5 text-accent'
                  : 'border-border hover:border-border-hover',
              )}
            >
              <Copy className="w-6 h-6" />
              <span className="text-sm font-medium">Copy</span>
              <span className="text-xs text-text-muted">Keep originals</span>
            </button>
            <button
              onClick={() => updateSettings({ move: true })}
              className={cn(
                'flex flex-col items-center gap-2 p-4 rounded-xl border transition-colors',
                settings.move
                  ? 'border-accent bg-accent/5 text-accent'
                  : 'border-border hover:border-border-hover',
              )}
            >
              <Move className="w-6 h-6" />
              <span className="text-sm font-medium">Move</span>
              <span className="text-xs text-text-muted">Relocate files</span>
            </button>
          </div>
        </div>
      </div>

      {/* Start button */}
      <button
        onClick={handleStart}
        className="w-full flex items-center justify-center gap-3 px-6 py-4 rounded-xl bg-accent text-background text-base font-semibold hover:bg-accent-hover transition-colors shadow-lg shadow-accent/20"
      >
        <Play className="w-5 h-5" />
        Start Processing {currentSession.image_count} Images
      </button>
    </PageContainer>
  )
}
