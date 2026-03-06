export interface ProcessingSettings {
  blur_threshold: number
  overexposure_threshold: number
  underexposure_threshold: number
  workers: number
  move: boolean
  cluster: boolean
  fast: boolean
  similarity_threshold: number
  min_cluster_size: number
  batch_size: number
  hash_threshold: number
}

export interface SessionSummary {
  total: number
  good: number
  blurry: number
  overexposed: number
  underexposed: number
  errors: number
  num_clusters?: number
  num_unique?: number
  num_best_picks?: number
}

export interface Session {
  id: string
  name: string
  input_path: string
  output_path: string
  status: 'pending' | 'processing' | 'complete' | 'error' | 'cancelled'
  created_at: string
  updated_at: string
  settings?: ProcessingSettings
  summary?: SessionSummary
  image_count: number
}

export interface QualityResult {
  filename: string
  original_path: string
  category: 'good' | 'blurry' | 'overexposed' | 'underexposed'
  sharpness_laplacian: number
  sharpness_tenengrad: number
  brightness_mean: number
  brightness_std: number
  noise_estimate: number
  quality_score: number
  is_blurry: boolean
  is_overexposed: boolean
  is_underexposed: boolean
}

export interface ClusterAssignment {
  filename: string
  original_path: string
  cluster_id: number | 'unique'
  cluster_folder: string
}

export interface BestPick {
  filename: string
  original_path: string
  source: string
  cluster_id: number
  quality_score: number
  selection_reason: string
}

export interface FolderEntry {
  name: string
  path: string
  is_dir: boolean
  image_count?: number
}

export interface BrowseResponse {
  current_path: string
  parent_path?: string
  entries: FolderEntry[]
  drives?: string[]
}

export interface ResultsData {
  quality_results: QualityResult[]
  cluster_assignments: ClusterAssignment[]
  best_picks: BestPick[]
  summary: SessionSummary
  clusters: Record<string, QualityResult[]>
}

export interface ProgressEvent {
  type: 'phase_start' | 'progress' | 'phase_complete' | 'pipeline_complete' | 'error' | 'cancelled' | 'heartbeat' | 'session_info' | 'warning'
  phase?: string
  current?: number
  total?: number
  image?: string
  category?: string
  score?: number
  status?: string
  step?: string
  stats?: Record<string, number>
  summary?: SessionSummary
  message?: string
  image_count?: number
}

export const DEFAULT_SETTINGS: ProcessingSettings = {
  blur_threshold: 100,
  overexposure_threshold: 220,
  underexposure_threshold: 40,
  workers: 4,
  move: false,
  cluster: true,
  fast: false,
  similarity_threshold: 0.25,
  min_cluster_size: 2,
  batch_size: 32,
  hash_threshold: 15,
}
