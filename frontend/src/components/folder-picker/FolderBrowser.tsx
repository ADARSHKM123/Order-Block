import { useState } from 'react'
import { api } from '@/api/client'
import { cn } from '@/lib/utils'
import {
  FolderOpen,
  FolderSearch,
  Loader2,
  X,
} from 'lucide-react'

interface Props {
  onSelect: (path: string) => void
  selectedPath?: string
  label: string
}

export function FolderBrowser({ onSelect, selectedPath, label }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleBrowse = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await api.openFolderDialog()
      if (res.path) {
        onSelect(res.path)
      }
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const handleClear = () => {
    onSelect('')
  }

  return (
    <div
      className={cn(
        'rounded-2xl bg-white shadow-sm overflow-hidden transition-all duration-200 dark:bg-[#1a1a1e] dark:shadow-none dark:border dark:border-white/5',
        selectedPath && 'ring-2 ring-accent/20',
      )}
    >
      <div className="p-6">
        <p className="text-sm font-medium text-text-secondary mb-4">{label}</p>

        {/* Selected path display */}
        {selectedPath ? (
          <div className="flex items-center gap-3 mb-4 px-4 py-3 rounded-xl bg-accent/5 border border-accent/10">
            <FolderOpen className="w-5 h-5 text-accent shrink-0" />
            <span className="text-sm text-text-primary font-medium truncate flex-1">
              {selectedPath}
            </span>
            <button
              onClick={handleClear}
              className="p-1 rounded-full hover:bg-gray-200/50 dark:hover:bg-white/10 text-text-muted hover:text-text-primary transition-colors shrink-0"
              title="Clear selection"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3 mb-4 px-4 py-3 rounded-xl bg-gray-50 dark:bg-white/5 border border-dashed border-gray-200 dark:border-white/10">
            <FolderSearch className="w-5 h-5 text-text-muted shrink-0" />
            <span className="text-sm text-text-muted">No folder selected</span>
          </div>
        )}

        {error && (
          <p className="text-sm text-overexposed mb-3">{error}</p>
        )}

        {/* Browse button */}
        <button
          onClick={handleBrowse}
          disabled={loading}
          className={cn(
            'w-full flex items-center justify-center gap-2.5 px-5 py-3 rounded-xl text-sm font-semibold transition-all duration-200',
            selectedPath
              ? 'bg-gray-100 text-text-secondary hover:bg-gray-200 dark:bg-white/5 dark:hover:bg-white/10'
              : 'bg-gray-900 text-white hover:bg-gray-800 shadow-sm dark:bg-white dark:text-gray-900 dark:hover:bg-gray-100',
          )}
        >
          {loading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              <FolderSearch className="w-4 h-4" />
              {selectedPath ? 'Change Folder' : 'Browse Folder'}
            </>
          )}
        </button>
      </div>
    </div>
  )
}
