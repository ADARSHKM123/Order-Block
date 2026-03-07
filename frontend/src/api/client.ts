import type { BrowseResponse, ResultsData, Session } from './types'

const BASE = '/api'

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  // Sessions
  createSession: (input_path: string, output_path: string, name?: string) =>
    request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ input_path, output_path, name }),
    }),

  listSessions: () => request<Session[]>('/sessions'),

  getSession: (id: string) => request<Session>(`/sessions/${id}`),

  deleteSession: (id: string) =>
    request(`/sessions/${id}`, { method: 'DELETE' }),

  // Processing
  startProcessing: (id: string, settings: Record<string, unknown>) =>
    request(`/sessions/${id}/process`, {
      method: 'POST',
      body: JSON.stringify({ settings }),
    }),

  cancelProcessing: (id: string) =>
    request(`/sessions/${id}/cancel`, { method: 'POST' }),

  // Results
  getResults: (id: string) => request<ResultsData>(`/sessions/${id}/results`),

  // Overrides
  saveOverrides: (id: string, overrides: Record<string, string>) =>
    request(`/sessions/${id}/overrides`, {
      method: 'PUT',
      body: JSON.stringify({ overrides }),
    }),

  // Folder browsing
  browse: (path?: string) =>
    request<BrowseResponse>('/browse', {
      method: 'POST',
      body: JSON.stringify({ path }),
    }),

  // Native folder dialog
  openFolderDialog: () =>
    request<{ path: string | null }>('/browse/dialog', {
      method: 'POST',
    }),

  // Image URLs
  imageUrl: (sessionId: string, filename: string, size?: string) => {
    const params = size ? `?size=${size}` : ''
    return `${BASE}/sessions/${sessionId}/images/${encodeURIComponent(filename)}${params}`
  },
}
