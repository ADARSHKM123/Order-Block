import { useMemo, useState } from 'react'
import { useSessionStore } from '@/stores/session-store'
import { ImageCard } from './ImageCard'
import { api } from '@/api/client'
import type { QualityResult } from '@/api/types'
import { Layers, ChevronDown, ChevronRight, Star } from 'lucide-react'

export function ClusterView() {
  const { clusters, bestPicks, currentSession, clusterAssignments, qualityResults } = useSessionStore()
  const [expandedClusters, setExpandedClusters] = useState<Set<string>>(new Set())
  const [overrides, setOverrides] = useState<Record<string, string>>({})

  const resultsByName = useMemo(() => {
    const map: Record<string, QualityResult> = {}
    qualityResults.forEach((r) => (map[r.filename] = r))
    return map
  }, [qualityResults])

  const uniqueImages = useMemo(() => {
    return clusterAssignments
      .filter((a) => a.cluster_id === 'unique')
      .map((a) => resultsByName[a.filename])
      .filter(Boolean)
  }, [clusterAssignments, resultsByName])

  const clusterEntries = useMemo(() => {
    return Object.entries(clusters)
      .map(([id, members]) => ({
        id,
        members,
        bestPick: bestPicks.find((p) => String(p.cluster_id) === id),
      }))
      .sort((a, b) => b.members.length - a.members.length)
  }, [clusters, bestPicks])

  if (!currentSession) return null

  const toggleCluster = (id: string) => {
    setExpandedClusters((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleOverride = async (clusterId: string, filename: string) => {
    const newOverrides = { ...overrides, [clusterId]: filename }
    setOverrides(newOverrides)
    await api.saveOverrides(currentSession.id, newOverrides)
  }

  const getBestPickName = (clusterId: string): string => {
    return overrides[clusterId] || clusterEntries.find((c) => c.id === clusterId)?.bestPick?.filename || ''
  }

  return (
    <div className="space-y-3">
      <p className="text-sm text-text-muted mb-4">
        {clusterEntries.length} groups found · {uniqueImages.length} unique images · Click an image to select it as the best pick
      </p>

      {clusterEntries.map(({ id, members, bestPick }) => {
        const isExpanded = expandedClusters.has(id)
        const currentBest = getBestPickName(id)

        return (
          <div key={id} className="border border-border rounded-xl bg-surface overflow-hidden">
            {/* Header */}
            <button
              onClick={() => toggleCluster(id)}
              className="w-full flex items-center gap-3 px-4 py-3 hover:bg-surface-hover transition-colors"
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4 text-text-muted" />
              ) : (
                <ChevronRight className="w-4 h-4 text-text-muted" />
              )}
              <Layers className="w-4 h-4 text-accent" />
              <span className="text-sm font-medium">
                Group {String(Number(id) + 1).padStart(3, '0')}
              </span>
              <span className="text-xs text-text-muted">
                {members.length} images
              </span>
              <span className="flex-1" />
              {bestPick && (
                <span className="flex items-center gap-1 text-xs text-accent">
                  <Star className="w-3 h-3" />
                  {currentBest || bestPick.filename}
                </span>
              )}
            </button>

            {/* Expanded: horizontal scroll of images */}
            {isExpanded && (
              <div className="border-t border-border px-4 py-3">
                <div className="flex gap-2 overflow-x-auto pb-2">
                  {members.map((member) => {
                    const isBest = member.filename === currentBest
                    return (
                      <div key={member.filename} className="shrink-0">
                        <ImageCard
                          image={member}
                          sessionId={currentSession.id}
                          selected={isBest}
                          onClick={() => handleOverride(id, member.filename)}
                          size="sm"
                          showCategory={false}
                        />
                        <p className="text-[10px] text-text-muted mt-1 truncate max-w-[96px]">
                          {member.filename}
                        </p>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )
      })}

      {/* Unique images */}
      {uniqueImages.length > 0 && (
        <div className="mt-8">
          <h3 className="text-sm font-medium text-text-muted mb-3">
            Unique Images ({uniqueImages.length})
          </h3>
          <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-10 gap-2">
            {uniqueImages.map((img) => (
              <ImageCard
                key={img.filename}
                image={img}
                sessionId={currentSession.id}
                size="sm"
                showCategory={false}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
