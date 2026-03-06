import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  LayoutDashboard,
  Settings,
  Loader,
  Images,
  Sun,
  Moon,
  Camera,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'
import { useState } from 'react'
import { useSettingsStore } from '@/stores/settings-store'
import { useSessionStore } from '@/stores/session-store'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/settings', icon: Settings, label: 'Settings' },
  { to: '/processing', icon: Loader, label: 'Processing' },
  { to: '/results', icon: Images, label: 'Results' },
]

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false)
  const { theme, toggleTheme } = useSettingsStore()
  const { currentSession } = useSessionStore()

  return (
    <aside
      className={cn(
        'flex flex-col h-screen border-r border-border bg-surface transition-all duration-200',
        collapsed ? 'w-16' : 'w-56',
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-5 border-b border-border">
        <Camera className="w-7 h-7 text-accent shrink-0" />
        {!collapsed && (
          <span className="text-lg font-semibold tracking-tight">
            Order Block
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1 px-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent/10 text-accent'
                  : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover',
              )
            }
          >
            <Icon className="w-5 h-5 shrink-0" />
            {!collapsed && label}
          </NavLink>
        ))}
      </nav>

      {/* Session info */}
      {currentSession && !collapsed && (
        <div className="px-4 py-3 border-t border-border">
          <p className="text-xs text-text-muted">Current Session</p>
          <p className="text-sm text-text-secondary truncate">{currentSession.name}</p>
          <p className="text-xs text-text-muted mt-0.5">
            {currentSession.image_count} images
          </p>
        </div>
      )}

      {/* Bottom controls */}
      <div className="border-t border-border p-2 flex items-center justify-between">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-hover transition-colors"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-hover transition-colors"
        >
          {collapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </button>
      </div>
    </aside>
  )
}
