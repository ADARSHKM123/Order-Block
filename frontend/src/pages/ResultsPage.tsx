import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { PageContainer } from '@/components/layout/PageContainer'
import { QualityOverview } from '@/components/results/QualityOverview'
import { ClusterView } from '@/components/results/ClusterView'
import { BestPicksGrid } from '@/components/results/BestPicksGrid'
import { useSessionStore } from '@/stores/session-store'
import { cn } from '@/lib/utils'
import { Search, Layers, Star, FolderOpen } from 'lucide-react'

const tabs = [
  { key: 'quality', label: 'Quality', icon: Search },
  { key: 'clusters', label: 'Clusters', icon: Layers },
  { key: 'best_picks', label: 'Best Picks', icon: Star },
] as const

type TabKey = (typeof tabs)[number]['key']

export function ResultsPage() {
  const navigate = useNavigate()
  const { currentSession, qualityResults, loadResults, summary } = useSessionStore()
  const [activeTab, setActiveTab] = useState<TabKey>('quality')

  useEffect(() => {
    if (currentSession && qualityResults.length === 0) {
      loadResults(currentSession.id)
    }
  }, [currentSession, qualityResults.length, loadResults])

  if (!currentSession) {
    return (
      <PageContainer title="Results" subtitle="No session selected">
        <div className="text-center py-20">
          <p className="text-text-muted mb-4">Process images first from the Dashboard.</p>
          <button onClick={() => navigate('/dashboard')} className="px-4 py-2 bg-accent text-white rounded-full font-medium hover:bg-accent-hover transition-colors">
            Go to Dashboard
          </button>
        </div>
      </PageContainer>
    )
  }

  if (currentSession.status !== 'complete' && qualityResults.length === 0) {
    return (
      <PageContainer title="Results" subtitle="Processing not complete">
        <div className="text-center py-20">
          <p className="text-text-muted mb-4">Wait for processing to finish.</p>
          <button onClick={() => navigate('/processing')} className="px-4 py-2 bg-accent text-white rounded-full font-medium hover:bg-accent-hover transition-colors">
            View Progress
          </button>
        </div>
      </PageContainer>
    )
  }

  return (
    <PageContainer
      title="Results"
      subtitle={summary ? `${summary.total} images analyzed` : ''}
      actions={
        <span className="flex items-center gap-1.5 text-sm text-text-muted">
          <FolderOpen className="w-4 h-4" />
          {currentSession.output_path}
        </span>
      }
    >
      {/* Pill Tabs */}
      <div className="flex items-center gap-1 mb-8 bg-gray-100 dark:bg-[#1a1a1e] p-1 rounded-xl w-fit">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key)}
            className={cn(
              'flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg transition-all duration-200',
              activeTab === key
                ? 'bg-white shadow-sm text-gray-900 dark:bg-[#242428] dark:text-white'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200',
            )}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {activeTab === 'quality' && <QualityOverview />}
      {activeTab === 'clusters' && <ClusterView />}
      {activeTab === 'best_picks' && <BestPicksGrid />}
    </PageContainer>
  )
}
