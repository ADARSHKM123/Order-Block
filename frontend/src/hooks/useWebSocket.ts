import { useEffect, useRef, useCallback } from 'react'
import type { ProgressEvent } from '../api/types'

export function useWebSocket(
  sessionId: string | null,
  onEvent: (event: ProgressEvent) => void,
  enabled: boolean = false,
) {
  const wsRef = useRef<WebSocket | null>(null)
  const onEventRef = useRef(onEvent)
  onEventRef.current = onEvent

  useEffect(() => {
    if (!sessionId || !enabled) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/api/sessions/${sessionId}/progress`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onmessage = (e) => {
      try {
        const event: ProgressEvent = JSON.parse(e.data)
        onEventRef.current(event)
      } catch {
        // ignore parse errors
      }
    }

    ws.onerror = () => {
      // Connection error, will reconnect on close
    }

    ws.onclose = () => {
      wsRef.current = null
    }

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [sessionId, enabled])

  const close = useCallback(() => {
    wsRef.current?.close()
    wsRef.current = null
  }, [])

  return { close }
}
