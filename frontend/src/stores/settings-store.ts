import { create } from 'zustand'
import type { ProcessingSettings } from '../api/types'
import { DEFAULT_SETTINGS } from '../api/types'

interface SettingsState {
  settings: ProcessingSettings
  theme: 'dark' | 'light'
  updateSettings: (partial: Partial<ProcessingSettings>) => void
  resetSettings: () => void
  toggleTheme: () => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  settings: { ...DEFAULT_SETTINGS },
  theme: 'light',

  updateSettings: (partial) =>
    set((s) => ({ settings: { ...s.settings, ...partial } })),

  resetSettings: () => set({ settings: { ...DEFAULT_SETTINGS } }),

  toggleTheme: () =>
    set((s) => {
      const next = s.theme === 'light' ? 'dark' : 'light'
      document.documentElement.classList.toggle('dark', next === 'dark')
      return { theme: next }
    }),
}))
