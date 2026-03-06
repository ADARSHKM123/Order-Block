import { useEffect, useCallback } from 'react'
import { api } from '@/api/client'
import type { QualityResult } from '@/api/types'
import { cn } from '@/lib/utils'
import { X, ChevronLeft, ChevronRight } from 'lucide-react'

interface Props {
  image: QualityResult
  sessionId: string
  onClose: () => void
  images?: QualityResult[]
  onNavigate?: (image: QualityResult) => void
}

export function Lightbox({ image, sessionId, onClose, images, onNavigate }: Props) {
  const currentIdx = images?.findIndex((i) => i.filename === image.filename) ?? -1

  const goNext = useCallback(() => {
    if (images && onNavigate && currentIdx < images.length - 1) {
      onNavigate(images[currentIdx + 1])
    }
  }, [images, onNavigate, currentIdx])

  const goPrev = useCallback(() => {
    if (images && onNavigate && currentIdx > 0) {
      onNavigate(images[currentIdx - 1])
    }
  }, [images, onNavigate, currentIdx])

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowRight') goNext()
      if (e.key === 'ArrowLeft') goPrev()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [onClose, goNext, goPrev])

  const categoryColors = {
    good: 'text-good',
    blurry: 'text-blurry',
    overexposed: 'text-overexposed',
    underexposed: 'text-underexposed',
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex" onClick={onClose}>
      {/* Close button */}
      <button
        onClick={onClose}
        className="absolute top-4 right-4 z-10 p-2 rounded-lg bg-white/10 hover:bg-white/20 text-white transition-colors"
      >
        <X className="w-5 h-5" />
      </button>

      {/* Previous */}
      {images && currentIdx > 0 && (
        <button
          onClick={(e) => { e.stopPropagation(); goPrev() }}
          className="absolute left-4 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
        >
          <ChevronLeft className="w-6 h-6" />
        </button>
      )}

      {/* Next */}
      {images && currentIdx < images.length - 1 && (
        <button
          onClick={(e) => { e.stopPropagation(); goNext() }}
          className="absolute right-4 top-1/2 -translate-y-1/2 z-10 p-3 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors"
        >
          <ChevronRight className="w-6 h-6" />
        </button>
      )}

      {/* Image */}
      <div className="flex-1 flex items-center justify-center p-8" onClick={(e) => e.stopPropagation()}>
        <img
          src={api.imageUrl(sessionId, image.filename)}
          alt={image.filename}
          className="max-w-full max-h-full object-contain rounded-lg"
        />
      </div>

      {/* Metrics panel */}
      <div
        className="w-72 bg-surface border-l border-border p-5 overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <h3 className="font-semibold mb-1 truncate">{image.filename}</h3>
        <p className={cn('text-sm mb-4', categoryColors[image.category])}>
          {image.category} · Score: {image.quality_score}
        </p>

        <div className="space-y-3">
          <MetricRow label="Sharpness (Laplacian)" value={image.sharpness_laplacian} />
          <MetricRow label="Sharpness (Tenengrad)" value={image.sharpness_tenengrad} />
          <MetricRow label="Brightness Mean" value={image.brightness_mean} />
          <MetricRow label="Brightness Std" value={image.brightness_std} />
          <MetricRow label="Noise Estimate" value={image.noise_estimate} />
        </div>

        <div className="mt-6 space-y-2 text-xs text-text-muted">
          <div className="flex items-center gap-2">
            <span className={image.is_blurry ? 'text-blurry' : 'text-good'}>
              {image.is_blurry ? 'Blurry' : 'Sharp'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className={image.is_overexposed ? 'text-overexposed' : 'text-good'}>
              {image.is_overexposed ? 'Overexposed' : 'Normal exposure'}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className={image.is_underexposed ? 'text-underexposed' : 'text-good'}>
              {image.is_underexposed ? 'Underexposed' : 'Normal exposure'}
            </span>
          </div>
        </div>

        {images && (
          <p className="mt-6 text-xs text-text-muted text-center">
            {currentIdx + 1} / {images.length} · Arrow keys to navigate
          </p>
        )}
      </div>
    </div>
  )
}

function MetricRow({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <p className="text-xs text-text-muted">{label}</p>
      <p className="text-sm font-mono">{value}</p>
    </div>
  )
}
