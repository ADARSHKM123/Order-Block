import { useState, useMemo } from 'react'
import { useSessionStore } from '@/stores/session-store'
import { ImageCard } from './ImageCard'
import { Lightbox } from '../compare/Lightbox'
import { cn } from '@/lib/utils'
import type { QualityResult } from '@/api/types'
import { CheckCircle, AlertTriangle, Sun, Moon } from 'lucide-react'

const categories = [
  { key: 'all', label: 'All', icon: null, color: '' },
  { key: 'good', label: 'Good', icon: CheckCircle, color: 'text-good' },
  { key: 'blurry', label: 'Blurry', icon: AlertTriangle, color: 'text-blurry' },
  { key: 'overexposed', label: 'Overexposed', icon: Sun, color: 'text-overexposed' },
  { key: 'underexposed', label: 'Underexposed', icon: Moon, color: 'text-underexposed' },
] as const

type SortKey = 'quality_score' | 'filename'

export function QualityOverview() {
  const { qualityResults, summary, currentSession } = useSessionStore()
  const [filter, setFilter] = useState<string>('all')
  const [sort, setSort] = useState<SortKey>('quality_score')
  const [sortDesc, setSortDesc] = useState(true)
  const [lightboxImage, setLightboxImage] = useState<QualityResult | null>(null)

  const filtered = useMemo(() => {
    let items = filter === 'all' ? qualityResults : qualityResults.filter((r) => r.category === filter)
    items = [...items].sort((a, b) => {
      const cmp = sort === 'quality_score' ? a.quality_score - b.quality_score : a.filename.localeCompare(b.filename)
      return sortDesc ? -cmp : cmp
    })
    return items
  }, [qualityResults, filter, sort, sortDesc])

  if (!currentSession) return null

  return (
    <div>
      {/* Summary badges */}
      {summary && (
        <div className="flex flex-wrap gap-3 mb-6">
          {categories.slice(1).map((cat) => {
            const count = summary[cat.key as keyof typeof summary] as number
            return (
              <button
                key={cat.key}
                onClick={() => setFilter(filter === cat.key ? 'all' : cat.key)}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-lg border transition-all duration-200 text-sm',
                  filter === cat.key
                    ? 'border-current bg-current/5'
                    : 'border-gray-200 hover:border-gray-300 dark:border-white/10 dark:hover:border-white/20',
                  cat.color,
                )}
              >
                {cat.icon && <cat.icon className="w-4 h-4" />}
                <span className="font-medium">{count}</span>
                <span className="text-text-muted">{cat.label}</span>
              </button>
            )
          })}
        </div>
      )}

      {/* Sort controls */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-sm text-text-muted">{filtered.length} images</span>
        <span className="text-gray-300 dark:text-gray-600">·</span>
        <button
          onClick={() => { setSort('quality_score'); setSortDesc(true) }}
          className={cn('text-sm', sort === 'quality_score' ? 'text-accent' : 'text-text-muted hover:text-text-primary')}
        >
          By Score
        </button>
        <button
          onClick={() => { setSort('filename'); setSortDesc(false) }}
          className={cn('text-sm', sort === 'filename' ? 'text-accent' : 'text-text-muted hover:text-text-primary')}
        >
          By Name
        </button>
      </div>

      {/* Image grid */}
      <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 xl:grid-cols-8 gap-2">
        {filtered.map((img) => (
          <ImageCard
            key={img.filename}
            image={img}
            sessionId={currentSession.id}
            onClick={() => setLightboxImage(img)}
          />
        ))}
      </div>

      {/* Lightbox */}
      {lightboxImage && (
        <Lightbox
          image={lightboxImage}
          sessionId={currentSession.id}
          onClose={() => setLightboxImage(null)}
          images={filtered}
          onNavigate={setLightboxImage}
        />
      )}
    </div>
  )
}
