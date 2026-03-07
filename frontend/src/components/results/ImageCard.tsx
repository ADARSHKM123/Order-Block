import { cn } from '@/lib/utils'
import { api } from '@/api/client'
import type { QualityResult } from '@/api/types'

interface Props {
  image: QualityResult
  sessionId: string
  selected?: boolean
  onClick?: () => void
  showScore?: boolean
  showCategory?: boolean
  size?: 'sm' | 'md' | 'lg'
}

const categoryColors = {
  good: 'bg-good/10 text-good border-good/20',
  blurry: 'bg-blurry/10 text-blurry border-blurry/20',
  overexposed: 'bg-overexposed/10 text-overexposed border-overexposed/20',
  underexposed: 'bg-underexposed/10 text-underexposed border-underexposed/20',
}

export function ImageCard({ image, sessionId, selected, onClick, showScore = true, showCategory = true, size = 'md' }: Props) {
  const sizeClass = {
    sm: 'w-24 h-24',
    md: 'w-full aspect-square',
    lg: 'w-full aspect-[4/3]',
  }[size]

  return (
    <div
      className={cn(
        'group relative rounded-lg overflow-hidden border transition-all duration-200 cursor-pointer',
        selected ? 'border-accent ring-2 ring-accent/30' : 'border-gray-200/50 hover:shadow-md dark:border-white/5',
      )}
      onClick={onClick}
    >
      <div className={cn('bg-gray-100 dark:bg-[#1c1c1f]', sizeClass)}>
        <img
          src={api.imageUrl(sessionId, image.filename, 'thumb')}
          alt={image.filename}
          className="w-full h-full object-cover"
          loading="lazy"
        />
      </div>

      {/* Overlay badges */}
      <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-2">
        <div className="flex items-center justify-between">
          {showCategory && (
            <span className={cn('text-[10px] px-1.5 py-0.5 rounded-full border', categoryColors[image.category])}>
              {image.category}
            </span>
          )}
          {showScore && (
            <span className="text-[10px] text-white/80 font-mono">
              {image.quality_score}
            </span>
          )}
        </div>
      </div>

      {/* Filename on hover */}
      <div className="absolute top-0 left-0 right-0 bg-gradient-to-b from-black/50 to-transparent p-2 opacity-0 group-hover:opacity-100 transition-opacity">
        <p className="text-[10px] text-white truncate">{image.filename}</p>
      </div>

      {selected && (
        <div className="absolute top-2 right-2">
          <div className="w-5 h-5 rounded-full bg-accent flex items-center justify-center">
            <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
        </div>
      )}
    </div>
  )
}
