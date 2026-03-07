import { create } from 'zustand'
import type { BestPick, ClusterAssignment, ProcessingSettings, ProgressEvent, QualityResult, Session, SessionSummary } from '../api/types'
import { api } from '../api/client'

interface ProcessingProgress {
  phase: string
  current: number
  total: number
  image?: string
  category?: string
  score?: number
  step?: string
}

interface ProcessedImage {
  filename: string
  category: string
  score: number
}

interface SessionState {
  // Session list
  sessions: Session[]
  currentSession: Session | null

  // Results
  qualityResults: QualityResult[]
  clusterAssignments: ClusterAssignment[]
  bestPicks: BestPick[]
  clusters: Record<string, QualityResult[]>
  summary: SessionSummary | null

  // Processing
  isProcessing: boolean
  progress: ProcessingProgress | null
  phaseStats: Record<string, Record<string, number>>
  processedImages: ProcessedImage[]
  warnings: string[]
  errorMessage: string | null

  // Actions
  loadSessions: () => Promise<void>
  createSession: (inputPath: string, outputPath: string, name?: string) => Promise<Session>
  setCurrentSession: (session: Session | null) => void
  loadResults: (sessionId: string) => Promise<void>
  startProcessing: (sessionId: string, settings: ProcessingSettings) => Promise<void>
  handleProgressEvent: (event: ProgressEvent) => void
  setProcessing: (v: boolean) => void
  deleteSession: (id: string) => Promise<void>
}

export const useSessionStore = create<SessionState>((set) => ({
  sessions: [],
  currentSession: null,
  qualityResults: [],
  clusterAssignments: [],
  bestPicks: [],
  clusters: {},
  summary: null,
  isProcessing: false,
  progress: null,
  phaseStats: {},
  processedImages: [],
  warnings: [],
  errorMessage: null,

  loadSessions: async () => {
    const sessions = await api.listSessions()
    set({ sessions })
  },

  createSession: async (inputPath, outputPath, name) => {
    const session = await api.createSession(inputPath, outputPath, name)
    set(s => ({ sessions: [session, ...s.sessions], currentSession: session }))
    return session
  },

  setCurrentSession: (session) => {
    set({
      currentSession: session,
      qualityResults: [],
      clusterAssignments: [],
      bestPicks: [],
      clusters: {},
      summary: null,
      progress: null,
      phaseStats: {},
      processedImages: [],
      warnings: [],
      errorMessage: null,
    })
  },

  loadResults: async (sessionId) => {
    const data = await api.getResults(sessionId)
    set({
      qualityResults: data.quality_results,
      clusterAssignments: data.cluster_assignments,
      bestPicks: data.best_picks,
      clusters: data.clusters,
      summary: data.summary,
    })
  },

  startProcessing: async (sessionId, settings) => {
    set({ isProcessing: true, progress: null, phaseStats: {}, processedImages: [], warnings: [], errorMessage: null })
    await api.startProcessing(sessionId, settings as unknown as Record<string, unknown>)
  },

  handleProgressEvent: (event) => {
    const { type } = event

    if (type === 'progress') {
      const newProgress: ProcessingProgress = {
        phase: event.phase || '',
        current: event.current || 0,
        total: event.total || 0,
        image: event.image,
        category: event.category,
        score: event.score,
        step: event.step,
      }

      // Accumulate processed images for the live mosaic
      if (event.phase === 'quality' && event.status === 'ok' && event.image && event.category) {
        set(s => ({
          progress: newProgress,
          processedImages: [
            ...s.processedImages,
            { filename: event.image!, category: event.category!, score: event.score ?? 0 },
          ],
        }))
      } else {
        set({ progress: newProgress })
      }
    } else if (type === 'phase_start') {
      set({
        progress: {
          phase: event.phase || '',
          current: 0,
          total: event.total || 0,
        },
      })
    } else if (type === 'phase_complete') {
      set(s => ({
        phaseStats: {
          ...s.phaseStats,
          [event.phase || '']: event.stats || {},
        },
      }))
    } else if (type === 'pipeline_complete') {
      set({
        isProcessing: false,
        summary: event.summary || null,
      })
    } else if (type === 'warning') {
      set(s => ({ warnings: [...s.warnings, event.message || 'Unknown warning'] }))
    } else if (type === 'error' || type === 'cancelled') {
      set({
        isProcessing: false,
        errorMessage: event.message || (type === 'cancelled' ? 'Processing cancelled' : 'Processing failed'),
      })
    }
  },

  setProcessing: (v) => set({ isProcessing: v }),

  deleteSession: async (id) => {
    await api.deleteSession(id)
    set(s => ({
      sessions: s.sessions.filter(sess => sess.id !== id),
      currentSession: s.currentSession?.id === id ? null : s.currentSession,
    }))
  },
}))
