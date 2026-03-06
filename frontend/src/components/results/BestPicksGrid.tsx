import { useMemo, useState } from 'react'
import { useSessionStore } from '@/stores/session-store'
import { ImageCard } from './ImageCard'
import { Lightbox } from '../compare/Lightbox'
import type { QualityResult } from '@/api/types'
import { Star, FolderOpen } from 'lucide-react'

export function BestPicksGrid() {
  const { bestPicks, qualityResults, currentSession } = useSessionStore()
  const [lightboxImage, setLightboxImage] = useState<QualityResult | null>(null)

  const resultsByName = useMemo(() => {
    const map: Record<string, QualityResult> = {}
    qualityResults.forEach((r) => (map[r.filename] = r))
    return map
  }, [qualityResults])

  const pickResults = useMemo(() => {
    return bestPicks
      .map((pick) => ({
        pick,
        result: resultsByName[pick.filename],
      }))
      .filter((p) => p.result)
  }, [bestPicks, resultsByName])

  if (!currentSession) return null

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Star className="w-5 h-5 text-accent" />
          <span className="text-sm text-text-secondary">
            {bestPicks.length} best picks selected
          </span>
        </div>
        {currentSession.output_path && (
          <span className="flex items-center gap-1.5 text-sm text-text-muted">
            <FolderOpen className="w-4 h-4" />
            {currentSession.output_path}/best_picks
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3">
        {pickResults.map(({ pick, result }) => (
          <div key={pick.filename} className="space-y-1.5">
            <ImageCard
              image={result}
              sessionId={currentSession.id}
              onClick={() => setLightboxImage(result)}
              size="md"
              showCategory
            />
            <div className="px-1">
              <p className="text-xs text-text-secondary truncate">{pick.filename}</p>
              <p className="text-[10px] text-text-muted">
                {pick.source} · Score: {pick.quality_score}
              </p>
              <p className="text-[10px] text-accent">{pick.selection_reason}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Lightbox */}
      {lightboxImage && (
        <Lightbox
          image={lightboxImage}
          sessionId={currentSession.id}
          onClose={() => setLightboxImage(null)}
          images={pickResults.map((p) => p.result)}
          onNavigate={setLightboxImage}
        />
      )}
    </div>
  )
}
