import { useState, useEffect } from 'react'
import { api } from '@/api/client'
import type { BrowseResponse } from '@/api/types'
import { cn } from '@/lib/utils'
import {
  Folder,
  FolderOpen,
  ChevronUp,
  HardDrive,
  Image,
  Check,
} from 'lucide-react'

interface Props {
  onSelect: (path: string) => void
  selectedPath?: string
  label: string
}

export function FolderBrowser({ onSelect, selectedPath, label }: Props) {
  const [data, setData] = useState<BrowseResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [inputPath, setInputPath] = useState(selectedPath || '')

  const browse = async (path?: string) => {
    setLoading(true)
    setError('')
    try {
      const res = await api.browse(path)
      setData(res)
      setInputPath(res.current_path)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    browse()
  }, [])

  const handleSubmitPath = (e: React.FormEvent) => {
    e.preventDefault()
    if (inputPath.trim()) browse(inputPath.trim())
  }

  const handleSelectCurrent = () => {
    if (data) onSelect(data.current_path)
  }

  return (
    <div className="border border-border rounded-xl bg-surface">
      <div className="px-4 py-3 border-b border-border">
        <p className="text-sm font-medium text-text-secondary">{label}</p>
        <form onSubmit={handleSubmitPath} className="mt-2 flex gap-2">
          <input
            type="text"
            value={inputPath}
            onChange={(e) => setInputPath(e.target.value)}
            className="flex-1 bg-background border border-border rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-accent transition-colors"
            placeholder="Enter path..."
          />
          <button
            type="submit"
            className="px-3 py-2 text-sm bg-surface-hover hover:bg-surface-active rounded-lg transition-colors"
          >
            Go
          </button>
        </form>
      </div>

      {error && (
        <div className="px-4 py-2 text-sm text-overexposed bg-overexposed/10">
          {error}
        </div>
      )}

      {/* Drives (Windows) */}
      {data?.drives && (
        <div className="px-4 py-2 border-b border-border flex gap-2 flex-wrap">
          {data.drives.map((drive) => (
            <button
              key={drive}
              onClick={() => browse(drive)}
              className={cn(
                'flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors',
                data.current_path.startsWith(drive)
                  ? 'bg-accent/10 text-accent'
                  : 'text-text-secondary hover:bg-surface-hover',
              )}
            >
              <HardDrive className="w-3.5 h-3.5" />
              {drive}
            </button>
          ))}
        </div>
      )}

      {/* Navigation */}
      <div className="px-4 py-2 border-b border-border flex items-center gap-2">
        {data?.parent_path && (
          <button
            onClick={() => browse(data.parent_path!)}
            className="flex items-center gap-1 text-sm text-text-secondary hover:text-text-primary transition-colors"
          >
            <ChevronUp className="w-4 h-4" />
            Up
          </button>
        )}
        <span className="text-sm text-text-muted truncate flex-1">
          {data?.current_path}
        </span>
        <button
          onClick={handleSelectCurrent}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-accent text-background font-medium hover:bg-accent-hover transition-colors"
        >
          <Check className="w-3.5 h-3.5" />
          Select
        </button>
      </div>

      {/* File list */}
      <div className="max-h-64 overflow-auto">
        {loading ? (
          <div className="px-4 py-8 text-center text-text-muted text-sm">
            Loading...
          </div>
        ) : (
          data?.entries
            .filter((e) => e.is_dir)
            .map((entry) => (
              <button
                key={entry.path}
                onClick={() => browse(entry.path)}
                className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-surface-hover transition-colors text-left"
              >
                <Folder className="w-4 h-4 text-accent shrink-0" />
                <span className="text-sm flex-1 truncate">{entry.name}</span>
                {entry.image_count != null && entry.image_count > 0 && (
                  <span className="flex items-center gap-1 text-xs text-text-muted">
                    <Image className="w-3 h-3" />
                    {entry.image_count}
                  </span>
                )}
              </button>
            ))
        )}
      </div>

      {/* Selected path display */}
      {selectedPath && (
        <div className="px-4 py-2.5 border-t border-border bg-accent/5">
          <div className="flex items-center gap-2">
            <FolderOpen className="w-4 h-4 text-accent" />
            <span className="text-sm text-accent truncate">{selectedPath}</span>
          </div>
        </div>
      )}
    </div>
  )
}
