import { NavLink } from 'react-router-dom'
import { cn } from '@/lib/utils'
import {
  Home,
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
  { to: '/', icon: Home, label: 'Home', end: true },
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
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
        'flex flex-col h-screen bg-white/80 dark:bg-[#141416]/90 backdrop-blur-sm shadow-[1px_0_0_0_rgba(0,0,0,0.06)] dark:shadow-[1px_0_0_0_rgba(255,255,255,0.04)] transition-all duration-300',
        collapsed ? 'w-16' : 'w-60',
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-3 px-4 py-6">
        <div className="w-8 h-8 rounded-xl bg-amber-500/10 flex items-center justify-center shrink-0">
          <Camera className="w-5 h-5 text-accent" />
        </div>
        {!collapsed && (
          <span className="text-base font-semibold tracking-tight text-text-primary">
            Order Block
          </span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-2 space-y-1 px-3">
        {navItems.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-full text-sm font-medium transition-all duration-200',
                isActive
                  ? 'bg-gray-900/[0.06] text-gray-900 dark:bg-white/10 dark:text-white'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-900/[0.03] dark:text-gray-400 dark:hover:text-white dark:hover:bg-white/5',
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
        <div className="mx-3 mb-3 px-3 py-3 rounded-xl bg-gray-50 dark:bg-white/5">
          <p className="text-[11px] font-medium text-text-muted uppercase tracking-wider">Current Session</p>
          <p className="text-sm text-text-primary font-medium truncate mt-1">{currentSession.name}</p>
          <p className="text-xs text-text-muted mt-0.5">
            {currentSession.image_count} images
          </p>
        </div>
      )}

      {/* Bottom controls */}
      <div className="p-3 flex items-center justify-between">
        <button
          onClick={toggleTheme}
          className="p-2.5 rounded-full text-text-muted hover:text-text-primary hover:bg-gray-900/5 dark:hover:bg-white/5 transition-all duration-200"
          title={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}
        >
          {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
        </button>
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="p-2.5 rounded-full text-text-muted hover:text-text-primary hover:bg-gray-900/5 dark:hover:bg-white/5 transition-all duration-200"
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
