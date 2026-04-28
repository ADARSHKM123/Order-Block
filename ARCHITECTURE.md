# Order Block — Full Architecture Documentation

> A complete developer guide explaining every layer of the application:
> how the frontend renders UI, talks to the backend, processes images,
> streams real-time progress, serves thumbnails without uploading, and displays results.

---

## Table of Contents

1. [High-Level Overview](#1-high-level-overview)
2. [Project Structure](#2-project-structure)
3. [Frontend Deep Dive](#3-frontend-deep-dive)
   - 3.1 Entry Point & Routing
   - 3.2 Styling System (Tailwind CSS v4)
   - 3.3 State Management (Zustand)
   - 3.4 The API Client
   - 3.5 TypeScript Types
   - 3.6 Pages & Components
   - 3.7 WebSocket Hook
   - 3.8 Animations (Framer Motion)
4. [Backend Deep Dive](#4-backend-deep-dive)
   - 4.1 FastAPI Application
   - 4.2 Database Layer (SQLAlchemy + SQLite)
   - 4.3 API Routers
   - 4.4 Processing Service
   - 4.5 Thumbnail Service
   - 4.6 Session Manager
5. [Core Image Processing Library](#5-core-image-processing-library)
   - 5.1 Quality Analysis
   - 5.2 Similarity & Clustering
   - 5.3 Best Pick Selection
   - 5.4 File Management
6. [Complete Data Flow Walkthrough](#6-complete-data-flow-walkthrough)
   - 6.1 User Opens the App
   - 6.2 Creating a Session
   - 6.3 Configuring Settings
   - 6.4 Processing Pipeline (Real-Time)
   - 6.5 Viewing Results
   - 6.6 How Images Display Without Uploading
7. [The Vite Dev Proxy — Why It All Works Locally](#7-the-vite-dev-proxy)
8. [Key Techniques Explained](#8-key-techniques-explained)
9. [Technology Reference](#9-technology-reference)

---

## 1. High-Level Overview

```
+------------------+          HTTP/WS           +------------------+
|                  |  <--------------------->   |                  |
|   React Frontend |    localhost:5173          |  FastAPI Backend  |
|   (Vite + TS)    |    proxied to :8000        |  (Python)        |
|                  |                            |                  |
+------------------+                            +--------+---------+
        |                                                |
        | Renders UI                                     | Calls
        | in Browser                                     |
        v                                                v
+------------------+                            +------------------+
|  Zustand Store   |                            | order_block lib  |
|  (Global State)  |                            | (OpenCV, CLIP,   |
|                  |                            |  scikit-learn)   |
+------------------+                            +--------+---------+
                                                         |
                                                         | Reads/Writes
                                                         v
                                                +------------------+
                                                |  Local Filesystem |
                                                |  + SQLite DB      |
                                                |  (~/.order-block) |
                                                +------------------+
```

**The core idea**: The frontend and backend both run on your local machine.
Images are never "uploaded" — the backend reads them directly from your filesystem,
and the frontend fetches thumbnails from the backend via HTTP. This is what makes
the app fast and efficient.

---

## 2. Project Structure

```
image-sorter/
├── frontend/                    # React + TypeScript + Vite
│   ├── src/
│   │   ├── main.tsx             # App entry point
│   │   ├── App.tsx              # Router + lazy loading
│   │   ├── index.css            # Tailwind theme + dark mode
│   │   ├── api/
│   │   │   ├── client.ts        # All HTTP calls to backend
│   │   │   └── types.ts         # TypeScript interfaces
│   │   ├── stores/
│   │   │   ├── session-store.ts # Sessions, results, processing state
│   │   │   └── settings-store.ts# Quality thresholds, theme
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts  # Real-time progress connection
│   │   ├── pages/
│   │   │   ├── HeroPage.tsx     # Landing page with animation
│   │   │   ├── DashboardPage.tsx# Session management
│   │   │   ├── SettingsPage.tsx # Processing configuration
│   │   │   ├── ProcessingPage.tsx# Live progress visualization
│   │   │   └── ResultsPage.tsx  # Quality/Clusters/Best Picks tabs
│   │   ├── components/
│   │   │   ├── layout/          # Sidebar, PageContainer
│   │   │   ├── folder-picker/   # FolderBrowser (native dialog)
│   │   │   ├── results/         # ImageCard, ClusterView, etc.
│   │   │   ├── compare/         # Lightbox
│   │   │   └── ui/              # scroll-morph-hero
│   │   └── lib/
│   │       └── utils.ts         # cn() class merge utility
│   ├── vite.config.ts           # Dev server + proxy config
│   └── package.json             # Dependencies
│
├── server/                      # FastAPI backend
│   ├── main.py                  # App creation + startup
│   ├── config.py                # Settings (port, data dir)
│   ├── models.py                # Pydantic request/response schemas
│   ├── routers/
│   │   ├── sessions.py          # Session CRUD + folder browsing
│   │   ├── processing.py        # Start/cancel + WebSocket progress
│   │   └── images.py            # Results + image/thumbnail serving
│   ├── services/
│   │   ├── processing_service.py# Pipeline orchestration
│   │   ├── thumbnail_service.py # On-demand thumbnail generation
│   │   └── session_manager.py   # Database operations
│   └── database/
│       ├── connection.py        # SQLite setup
│       └── models.py            # SQLAlchemy ORM model
│
├── order_block/                 # Core image processing library
│   ├── pipeline.py              # Main processing pipeline
│   ├── utils.py                 # Image discovery + loading
│   ├── file_manager.py          # Copy/move files
│   ├── reporter.py              # Write CSV/JSON reports
│   ├── quality/
│   │   ├── analyzer.py          # OpenCV quality metrics
│   │   └── scorer.py            # Composite quality score
│   ├── similarity/
│   │   ├── embeddings.py        # CLIP visual embeddings
│   │   ├── hashing.py           # Perceptual hash clustering
│   │   └── clustering.py        # DBSCAN clustering
│   └── selection/
│       └── best_pick.py         # Best image per cluster
│
└── requirements.txt             # Python dependencies
```

---

## 3. Frontend Deep Dive

### 3.1 Entry Point & Routing

**`main.tsx`** — The very first file the browser executes:

```tsx
import { BrowserRouter } from 'react-router-dom'
import App from './App'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
)
```

**What's happening:**
- `BrowserRouter` enables client-side routing (URL changes without full page reloads)
- `StrictMode` helps catch bugs during development
- React mounts everything into the `#root` div in `index.html`

**`App.tsx`** — The router structure:

```tsx
// Pages are lazy-loaded (code-split into separate JS chunks)
const DashboardPage = lazy(() =>
  import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage }))
)

function AppLayout() {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <Suspense fallback={<PageLoader />}>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/settings"  element={<SettingsPage />} />
            ...
          </Routes>
        </AnimatePresence>
      </Suspense>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/"   element={<HeroPage />} />   {/* Full-screen, no sidebar */}
      <Route path="/*"  element={<AppLayout />} />   {/* Sidebar + page */}
    </Routes>
  )
}
```

**Key concepts:**
- **`lazy()`** — Splits each page into its own JS bundle. The browser only downloads
  the Dashboard code when you navigate there, not when the app first loads.
- **`Suspense`** — Shows a loading spinner while the lazy chunk downloads.
- **`AnimatePresence`** — Framer Motion wrapper that enables exit animations when
  routes change (pages fade out before the next one fades in).
- **Two route levels**: The hero page renders full-screen (no sidebar). Everything else
  renders inside `AppLayout` which includes the sidebar.

### 3.2 Styling System (Tailwind CSS v4)

**`index.css`** defines the design system:

```css
@import "tailwindcss";

/* Tell Tailwind: dark: classes only activate with .dark class, NOT system preference */
@custom-variant dark (&:where(.dark, .dark *));

@theme {
  --color-background: #FAFAFA;      /* Page background */
  --color-surface: #FFFFFF;          /* Card/panel backgrounds */
  --color-text-primary: #111827;     /* Main text color */
  --color-accent: #f59e0b;          /* Orange accent */
  --color-good: #22c55e;            /* Green for good images */
  --color-blurry: #f59e0b;          /* Orange for blurry */
  --color-overexposed: #ef4444;     /* Red for overexposed */
  --color-underexposed: #3b82f6;    /* Blue for underexposed */
  ...
}
```

**How it works:**
1. `@theme` defines CSS custom properties that become first-class Tailwind utilities.
   Writing `bg-background` in a component generates `background-color: var(--color-background)`.
2. The `.dark` class overrides these variables with dark colors.
3. `@custom-variant dark` is critical — without it, Tailwind uses the operating system's
   dark mode preference. With it, `dark:bg-[#1a1a1e]` only activates when `.dark` is on the HTML element.

**The `cn()` utility** (`lib/utils.ts`):
```ts
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```
This merges conditional class names intelligently. For example:
```tsx
cn('px-4 py-2', isActive && 'bg-accent text-white', !isActive && 'bg-gray-100')
// If isActive=true:  "px-4 py-2 bg-accent text-white"
// If isActive=false: "px-4 py-2 bg-gray-100"
```

### 3.3 State Management (Zustand)

Zustand is a lightweight alternative to Redux. It creates a global store
that any component can read from or write to.

**`settings-store.ts`** — Simple settings:
```ts
export const useSettingsStore = create<SettingsState>((set) => ({
  settings: { ...DEFAULT_SETTINGS },  // blur_threshold: 100, etc.
  theme: 'light',

  updateSettings: (partial) =>
    set((s) => ({ settings: { ...s.settings, ...partial } })),

  toggleTheme: () =>
    set((s) => {
      const next = s.theme === 'light' ? 'dark' : 'light'
      document.documentElement.classList.toggle('dark', next === 'dark')
      return { theme: next }
    }),
}))
```

**How components use it:**
```tsx
function MyComponent() {
  const { settings, updateSettings } = useSettingsStore()
  // settings.blur_threshold is always current
  // updateSettings({ blur_threshold: 150 }) updates globally
}
```

**`session-store.ts`** — The main application state:
```ts
export const useSessionStore = create<SessionState>((set, get) => ({
  // Data
  sessions: [],
  currentSession: null,
  qualityResults: [],
  clusters: {},
  bestPicks: [],

  // Processing state
  isProcessing: false,
  progress: null,
  processedImages: [],   // Accumulates images for live mosaic

  // Actions
  loadSessions: async () => {
    const sessions = await api.listSessions()
    set({ sessions })
  },

  handleProgressEvent: (event) => {
    // Called by WebSocket hook for each incoming event
    if (event.type === 'progress') {
      set((s) => ({
        progress: event,
        processedImages: event.image
          ? [...s.processedImages, event.image]
          : s.processedImages,
      }))
    }
    // ... handle phase_start, phase_complete, etc.
  },
}))
```

**Why Zustand instead of React Context?**
- No Provider wrapper needed
- No unnecessary re-renders (components only re-render when their specific slice changes)
- Simple API: `create()` returns a hook

### 3.4 The API Client

**`api/client.ts`** — Every HTTP call to the backend:

```ts
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
  createSession: (input_path, output_path) =>
    request<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify({ input_path, output_path }),
    }),

  openFolderDialog: () =>
    request<{ path: string | null }>('/browse/dialog', { method: 'POST' }),

  imageUrl: (sessionId, filename, size?) =>
    `${BASE}/sessions/${sessionId}/images/${encodeURIComponent(filename)}?size=${size}`,
  ...
}
```

**Key pattern**: The `request<T>()` generic function handles all HTTP calls:
1. Sends JSON to `/api/...`
2. Checks for errors
3. Returns typed response

**Note about `imageUrl()`**: This doesn't make an HTTP call — it returns a URL string.
When you use it as an `<img src={...}>`, the browser makes the HTTP request automatically.

### 3.5 TypeScript Types

**`api/types.ts`** — Shared contracts between frontend and backend:

```ts
export interface QualityResult {
  filename: string
  original_path: string
  category: 'good' | 'blurry' | 'overexposed' | 'underexposed'
  quality_score: number
  sharpness_laplacian: number
  sharpness_tenengrad: number
  brightness_mean: number
  brightness_std: number
  noise_estimate: number
  is_blurry: boolean
  is_overexposed: boolean
  is_underexposed: boolean
}

export interface ProgressEvent {
  type: 'progress' | 'phase_start' | 'phase_complete' | 'pipeline_complete' | ...
  phase?: string
  current?: number
  total?: number
  image?: { filename: string; category: string; score: number }
  ...
}
```

These types mirror the Pydantic models on the backend, ensuring type safety end-to-end.

### 3.6 Pages & Components

Each page follows a consistent pattern:

```tsx
export function DashboardPage() {
  // 1. Get state and actions from Zustand
  const { sessions, loadSessions } = useSessionStore()

  // 2. Load data on mount
  useEffect(() => { loadSessions() }, [])

  // 3. Render inside PageContainer (adds title, animation, padding)
  return (
    <PageContainer title="Dashboard" subtitle="Select a folder...">
      {/* Folder pickers, session cards, etc. */}
    </PageContainer>
  )
}
```

**PageContainer** wraps every page with:
- A title/subtitle header
- Framer Motion entrance animation (fade + slide up)
- Max-width container with padding

### 3.7 WebSocket Hook

**`hooks/useWebSocket.ts`** — Real-time progress updates:

```ts
export function useWebSocket(
  sessionId: string | null,
  onEvent: (event: ProgressEvent) => void,
  enabled: boolean,
) {
  useEffect(() => {
    if (!sessionId || !enabled) return

    // Build WebSocket URL from current page location
    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const ws = new WebSocket(
      `${protocol}://${window.location.host}/api/sessions/${sessionId}/progress`
    )

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      onEvent(data)  // Passes to session-store's handleProgressEvent
    }

    return () => ws.close()  // Cleanup when component unmounts
  }, [sessionId, enabled])
}
```

**How it connects to the processing page:**
1. `ProcessingPage` calls `useWebSocket(currentSession.id, onEvent, isProcessing)`
2. The WebSocket connects to the backend
3. Backend pushes events as JSON: `{ type: "progress", current: 5, total: 79, image: {...} }`
4. `onEvent` calls `handleProgressEvent` in the session store
5. Store updates `progress`, `processedImages`, `phaseStats`
6. React re-renders the progress bar, counters, and image mosaic

### 3.8 Animations (Framer Motion)

The hero page uses Framer Motion extensively:

```tsx
// Spring-based card animation
<motion.div
  animate={{ x: target.x, y: target.y, rotate: target.rotation }}
  transition={{ type: "spring", stiffness: 40, damping: 15 }}
/>

// Scroll-driven morph (circle → arc)
const morphProgress = useTransform(virtualScroll, [0, 600], [0, 1])
const smoothMorph = useSpring(morphProgress, { stiffness: 40, damping: 20 })

// Content fades in when arc is formed
const contentOpacity = useTransform(smoothMorph, [0.8, 1], [0, 1])
```

**Virtual scroll**: The hero captures wheel events and maps them to a 0-3000 range.
This drives two animations:
1. **Morph** (0-600): Circle → Bottom arc
2. **Rotation** (600-3000): Cards shuffle along the arc

---

## 4. Backend Deep Dive

### 4.1 FastAPI Application

**`server/main.py`**:
```python
app = FastAPI(title="Order Block", lifespan=lifespan)

# Allow frontend dev server to make cross-origin requests
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"])

# Register route handlers
app.include_router(sessions_router)
app.include_router(processing_router)
app.include_router(images_router)
```

**Why FastAPI?**
- Automatic API documentation (Swagger at `/docs`)
- Async support (WebSockets, background tasks)
- Pydantic integration (request/response validation)
- Type hints generate OpenAPI schema automatically

### 4.2 Database Layer

**SQLite** stores session metadata (not images — those stay on your filesystem).

**`database/models.py`** — The ORM model:
```python
class SessionRecord(Base):
    __tablename__ = "sessions"

    id = Column(String, primary_key=True)           # UUID
    name = Column(String)                            # Auto-generated or user-provided
    input_path = Column(String, nullable=False)      # e.g. "C:\Users\Photos"
    output_path = Column(String, nullable=False)     # e.g. "C:\Users\Sorted"
    status = Column(String, default="pending")       # pending/processing/complete/error
    image_count = Column(Integer, default=0)

    # Results stored as JSON strings (flexible schema)
    results_json = Column(Text)              # Quality results array
    clusters_json = Column(Text)             # Cluster groupings
    cluster_assignments_json = Column(Text)  # Image → cluster mapping
    best_picks_json = Column(Text)           # Selected best images
    summary_json = Column(Text)              # { total, good, blurry, ... }
    settings_json = Column(Text)             # Processing settings used
```

**Why JSON columns?** Results are complex nested structures. Instead of creating
many relational tables, we serialize them as JSON. This is a common pattern for
local-first apps where the data doesn't need SQL querying.

**`database/connection.py`**:
```python
DATABASE_URL = f"sqlite:///{settings.data_dir}/sessions.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """FastAPI dependency — provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 4.3 API Routers

#### Sessions Router (`/api/sessions`)

**Create session:**
```
POST /api/sessions
Body: { "input_path": "C:\\Photos", "output_path": "C:\\Sorted" }
Response: { "id": "abc-123", "name": "Photos", "status": "pending", "image_count": 79 }
```

The server validates the path exists, counts images, creates a DB record.

**Native folder dialog:**
```
POST /api/browse/dialog
Response: { "path": "C:\\Users\\ADARSH\\Pictures" }  // or { "path": null } if cancelled
```

This opens a real Windows file explorer dialog using Python's `tkinter`:
```python
root = tk.Tk()
root.withdraw()          # Hide the tkinter window
root.attributes("-topmost", True)  # Bring dialog to front of all windows
path = filedialog.askdirectory(title="Select Folder")
root.destroy()
```

Since FastAPI runs this as a sync function, it automatically runs in a thread pool
so it doesn't block the event loop.

#### Processing Router (`/api/sessions/{id}/process`)

**Start processing:**
```
POST /api/sessions/{id}/process
Body: { "settings": { "blur_threshold": 100, "cluster": true, ... } }
Response: { "ok": true }  // Returns immediately!
```

The actual processing runs in the background:
```python
@router.post("/sessions/{session_id}/process")
async def start_processing(session_id: str, req: StartProcessingRequest):
    # 1. Create processing service
    service = ProcessingService(session, req.settings)

    # 2. Store reference (for cancellation)
    _active_tasks[session_id] = service

    # 3. Create progress queue for WebSocket
    _progress_queues[session_id] = asyncio.Queue()

    # 4. Spawn background task (doesn't block this response)
    asyncio.create_task(_run_pipeline(session_id, service, db_session))

    return {"ok": True}  # Client gets response instantly
```

**WebSocket progress:**
```
WS /api/sessions/{id}/progress
```

```python
@router.websocket("/sessions/{session_id}/progress")
async def progress_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()

    queue = _progress_queues.get(session_id)
    while True:
        try:
            # Wait for next event from processing pipeline (30s timeout)
            event = await asyncio.wait_for(queue.get(), timeout=30)
            await websocket.send_json(event)

            # Close on terminal events
            if event["type"] in ("pipeline_complete", "error", "cancelled"):
                break
        except asyncio.TimeoutError:
            # Send heartbeat to keep connection alive
            await websocket.send_json({"type": "heartbeat"})
```

**How events flow from processing to browser:**
```
ProcessingService._phase1_sync()
  └→ puts {"type": "progress", "image": {...}} into queue
       └→ _run_with_progress() drains queue, calls callback
            └→ callback puts event into asyncio.Queue
                 └→ WebSocket handler reads queue, sends JSON
                      └→ Browser receives, calls onEvent()
                           └→ Zustand store updates
                                └→ React re-renders UI
```

#### Images Router (`/api/sessions/{id}/images/{filename}`)

This is how images display in the browser without being uploaded:

```
GET /api/sessions/{id}/images/photo.jpg?size=thumb
Response: JPEG binary data (200px thumbnail)
```

```python
@router.get("/sessions/{session_id}/images/{filename}")
async def serve_image(session_id, filename, size=None):
    # 1. Find the original file path from results
    results = get_session_results(db, session_id)
    original_path = None
    for r in results["quality_results"]:
        if r["filename"] == filename:
            original_path = r["original_path"]
            break

    # 2. Security: prevent path traversal (../../etc/passwd)
    if ".." in filename:
        raise HTTPException(400, "Invalid filename")

    # 3. Generate thumbnail or serve original
    if size and size in settings.thumbnail_sizes:
        thumb_path = thumbnail_service.get_thumbnail(
            original_path,
            settings.thumbnail_sizes[size]  # thumb=200px, medium=600px
        )
        return FileResponse(thumb_path, headers={"Cache-Control": "max-age=3600"})
    else:
        return FileResponse(original_path)
```

**On the frontend**, images are displayed like this:
```tsx
<img src={api.imageUrl(sessionId, image.filename, 'thumb')} />
// Generates: /api/sessions/abc-123/images/photo.jpg?size=thumb
```

The browser makes a GET request, the backend reads the file from disk,
generates a thumbnail (cached for future requests), and returns the binary data.
**No upload ever happens** — the backend has direct filesystem access.

### 4.4 Processing Service

The `ProcessingService` orchestrates three phases:

```python
async def run_pipeline(self):
    # Phase 1: Quality Assessment
    quality_results = await self._run_with_progress(self._phase1_sync)

    # Phase 2: Clustering (optional)
    if self.settings.cluster:
        clusters = await self._run_with_progress(self._phase2_sync)

    # Phase 3: Best Pick Selection
    best_picks = await self._run_with_progress(self._phase3_sync)

    return { "quality_results": ..., "clusters": ..., "best_picks": ... }
```

**`_run_with_progress()`** is the async/sync bridge:
```python
async def _run_with_progress(self, sync_fn):
    """Run blocking work in a thread while draining progress events."""
    progress_queue = queue.Queue()

    # Run CPU-heavy work in a thread pool (doesn't block event loop)
    future = asyncio.get_event_loop().run_in_executor(
        None, sync_fn, progress_queue
    )

    # Meanwhile, drain progress events and forward to WebSocket
    while not future.done():
        while not progress_queue.empty():
            event = progress_queue.get_nowait()
            await self.callback(event)  # Sends to WebSocket queue
        await asyncio.sleep(0.05)  # Yield to event loop

    return future.result()
```

### 4.5 Thumbnail Service

```python
def get_thumbnail(self, original_path: str, size: int) -> Path:
    # Cache key = MD5 of path + size
    cache_key = hashlib.md5(f"{original_path}:{size}".encode()).hexdigest()
    cached_path = self.cache_dir / f"{cache_key}.jpg"

    if cached_path.exists():
        return cached_path  # Cache hit!

    # Generate thumbnail
    img = Image.open(original_path)
    img.thumbnail((size, size), Image.LANCZOS)
    img.save(cached_path, "JPEG", quality=85)

    return cached_path
```

**Cache location**: `~/.order-block/thumbnails/`
First request for a thumbnail takes ~50ms (read + resize + save).
Subsequent requests serve from cache (~1ms).

### 4.6 Session Manager

Handles all database CRUD operations:

```python
def create_session(db, req):
    # Count images in input folder
    images = discover_images(Path(req.input_path))

    record = SessionRecord(
        id=str(uuid4()),
        name=req.name or Path(req.input_path).name,
        input_path=req.input_path,
        output_path=req.output_path,
        image_count=len(images),
        status="pending",
    )
    db.add(record)
    db.commit()
    return _to_response(record)

def save_session_results(db, session_id, results):
    record = db.query(SessionRecord).get(session_id)
    record.status = "complete"
    record.results_json = json.dumps(results["quality_results"])
    record.clusters_json = json.dumps(results["clusters"])
    record.best_picks_json = json.dumps(results["best_picks"])
    record.summary_json = json.dumps(results["summary"])
    db.commit()
```

---

## 5. Core Image Processing Library

### 5.1 Quality Analysis

**`quality/analyzer.py`** — OpenCV-based metrics:

```python
def analyze_image(path, blur_thresh=100, over_thresh=220, under_thresh=40):
    # Load image with OpenCV (BGR format)
    img = cv2.imread(str(path))

    # Resize if too large (performance)
    if max(img.shape[:2]) > 2048:
        scale = 2048 / max(img.shape[:2])
        img = cv2.resize(img, None, fx=scale, fy=scale)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 1. SHARPNESS — Laplacian variance
    #    High variance = sharp edges = sharp image
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    sharpness_lap = laplacian.var()

    # 2. SHARPNESS — Tenengrad (Sobel gradient)
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1)
    sharpness_ten = np.mean(gx**2 + gy**2)

    # 3. EXPOSURE — Brightness statistics
    brightness_mean = np.mean(gray)   # 0=black, 255=white
    brightness_std = np.std(gray)     # Low std = flat/washed out

    # 4. NOISE — Median Absolute Deviation on high-frequency
    highfreq = gray.astype(float) - cv2.GaussianBlur(gray, (7,7), 0).astype(float)
    noise = np.median(np.abs(highfreq))

    # 5. CLASSIFY
    is_blurry = sharpness_lap < blur_thresh
    is_overexposed = brightness_mean > over_thresh
    is_underexposed = brightness_mean < under_thresh

    return QualityMetrics(
        filename=path.name,
        sharpness_laplacian=sharpness_lap,
        brightness_mean=brightness_mean,
        is_blurry=is_blurry,
        ...
    )
```

**How blur detection works (Laplacian variance):**
```
Sharp image:          Blurry image:
  Edge pixels have       Edge pixels are
  HIGH contrast          LOW contrast
  [10, 200, 10]          [80, 120, 80]

  Laplacian detects      Laplacian detects
  big changes = HIGH     small changes = LOW
  variance (e.g. 500)    variance (e.g. 30)

  500 > threshold(100)   30 < threshold(100)
  → NOT blurry           → BLURRY
```

**`quality/scorer.py`** — Composite score (0-100):
```python
def compute_quality_score(metrics):
    # Sharpness: 50% weight
    sharpness_norm = min(metrics.sharpness_laplacian / 5, 100)

    # Exposure: 30% weight (ideal brightness 80-180)
    if 80 <= metrics.brightness_mean <= 180:
        exposure_score = 100
    else:
        distance = min(abs(metrics.brightness_mean - 80),
                       abs(metrics.brightness_mean - 180))
        exposure_score = max(0, 100 - distance)

    # Noise: 20% weight (lower is better)
    noise_score = max(0, 100 - metrics.noise_estimate * 2)

    return round(sharpness_norm * 0.5 + exposure_score * 0.3 + noise_score * 0.2)
```

### 5.2 Similarity & Clustering

**Two modes:**

**A) CLIP Embeddings (Accurate)**
```python
# Uses OpenAI's CLIP model to understand image content
model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# Each image → 512-dimensional vector
# Similar images have similar vectors (cosine similarity > threshold)
embeddings = extract_embeddings(image_paths)  # Shape: (n_images, 512)

# DBSCAN clustering: groups images with cosine similarity > 0.75
cluster_labels = cluster_embeddings(embeddings, eps=0.25)
```

**B) Perceptual Hashing (Fast)**
```python
# Each image → 64-bit hash
hash_a = imagehash.phash(Image.open("photo1.jpg"))
hash_b = imagehash.phash(Image.open("photo2.jpg"))

# Compare: hamming distance < threshold = similar
distance = hash_a - hash_b  # e.g. 3 (out of 64 bits differ)
if distance < 15:
    # Same cluster!
```

Uses union-find algorithm to build clusters efficiently.

### 5.3 Best Pick Selection

```python
def select_best_picks(clusters, quality_results):
    picks = []

    for cluster_id, members in clusters.items():
        # Sort by quality score (highest first)
        ranked = sorted(members, key=lambda m: m.quality_score, reverse=True)

        best = ranked[0]

        # Tiebreaker: if top 2 are within 5 points,
        # prefer the one with higher sharpness
        if len(ranked) > 1:
            if ranked[0].quality_score - ranked[1].quality_score <= 5:
                if ranked[1].sharpness_laplacian > ranked[0].sharpness_laplacian:
                    best = ranked[1]

        picks.append({
            "filename": best.filename,
            "cluster_id": cluster_id,
            "quality_score": best.quality_score,
            "selection_reason": "highest_quality" or "sharpness_tiebreaker",
        })

    # All unique (non-clustered) images are also included
    for img in unique_images:
        picks.append({ "filename": img.filename, "source": "unique" })

    return picks
```

### 5.4 File Management

```python
def create_output_structure(output_path, with_clusters=True):
    """Creates the folder structure for sorted images."""
    #
    # output/
    # ├── good/              # High quality images
    # ├── blurry/            # Detected as blurry
    # ├── overexposed/       # Too bright
    # ├── underexposed/      # Too dark
    # ├── clusters/
    # │   ├── group_001/     # Similar image group 1
    # │   ├── group_002/     # Similar image group 2
    # │   └── unique/        # One-of-a-kind images
    # └── best_picks/        # Best from each group
    #

def transfer_file(src, dest_dir, mode="copy"):
    """Copy or move a file, handling name collisions."""
    dest = dest_dir / src.name
    if dest.exists():
        # photo.jpg → photo_1.jpg → photo_2.jpg
        stem, suffix = dest.stem, dest.suffix
        counter = 1
        while dest.exists():
            dest = dest_dir / f"{stem}_{counter}{suffix}"
            counter += 1
    if mode == "copy":
        shutil.copy2(src, dest)
    else:
        shutil.move(src, dest)
```

---

## 6. Complete Data Flow Walkthrough

### 6.1 User Opens the App

```
Browser loads localhost:5173
  → Vite serves index.html + main.tsx bundle
  → React renders <BrowserRouter> → <App> → <HeroPage>
  → IntroAnimation plays: scatter → line → circle
  → User scrolls: circle morphs into arc
  → "Get Started" button fades in
  → Click: fade-out animation (300ms) → navigate('/dashboard')
```

### 6.2 Creating a Session

```
1. DashboardPage mounts
   → useEffect calls loadSessions()
   → GET /api/sessions → backend queries SQLite → returns session list

2. User clicks "Browse Folder"
   → POST /api/browse/dialog
   → Backend opens tkinter.filedialog.askdirectory()
   → Native Windows file explorer appears
   → User selects "C:\Photos"
   → Returns { "path": "C:\\Photos" }
   → FolderBrowser displays the path

3. User selects output folder similarly

4. User clicks "Continue to Settings"
   → POST /api/sessions
     Body: { "input_path": "C:\\Photos", "output_path": "C:\\Sorted" }
   → Backend:
     a. Validates C:\Photos exists and is a directory
     b. Creates C:\Sorted if it doesn't exist
     c. Counts images: 79 found
     d. Creates SessionRecord in SQLite
     e. Returns: { id: "abc-123", name: "Photos", image_count: 79, status: "pending" }
   → Frontend stores in Zustand → navigates to /settings
```

### 6.3 Configuring Settings

```
1. SettingsPage reads currentSession from store
   → Shows "Configure how 79 images will be analyzed"

2. User adjusts sliders:
   → Blur threshold: 100 → 120
   → updateSettings({ blur_threshold: 120 }) → Zustand store updates
   → Slider re-renders with new value (no API call — settings are in memory)

3. User clicks "Start Processing 79 Images"
   → startProcessing(sessionId, settings)
   → POST /api/sessions/abc-123/process
     Body: { settings: { blur_threshold: 120, cluster: true, ... } }
   → Backend returns { ok: true } immediately
   → Frontend navigates to /processing, sets isProcessing: true
```

### 6.4 Processing Pipeline (Real-Time)

This is the most complex flow. Here's what happens concurrently:

```
BACKEND (background task):                    FRONTEND (ProcessingPage):
─────────────────────────                     ──────────────────────────

Phase 1: Quality                              WebSocket connects to
┌─────────────────┐                           /api/sessions/abc-123/progress
│ For each image:  │                          │
│  1. Load with    │     ← event ──────────── │ Event: { type: "phase_start",
│     OpenCV       │                          │          phase: "quality" }
│  2. Compute:     │                          │ → Phase indicator: Quality (active)
│     - Laplacian  │                          │
│     - Brightness │                          │
│     - Noise      │                          │
│  3. Score 0-100  │     ← event ──────────── │ Event: { type: "progress",
│  4. Categorize   │                          │   current: 1, total: 79,
│  5. Copy file    │                          │   image: { filename: "IMG_001.jpg",
│     to output    │                          │     category: "good", score: 87 } }
│                  │                          │
│  Repeats 79x     │                          │ → Progress bar: 1/79 (1%)
│  (parallel with  │                          │ → Live counter: good=1
│   4 workers)     │                          │ → Image mosaic: adds thumbnail
└─────────────────┘                          │
                                              │ ... repeats 79 times ...
Phase 2: Clustering                           │
┌─────────────────┐     ← event ──────────── │ Event: { type: "phase_complete",
│ Load CLIP model  │                          │          phase: "quality",
│ Extract 512-dim  │                          │          stats: { good: 45, blurry: 20, ... } }
│   embeddings     │     ← event ──────────── │
│ Run DBSCAN       │                          │ Event: { type: "phase_start",
│ Group into       │                          │          phase: "clustering" }
│   clusters       │                          │ → Phase indicator: Clustering (active)
│ Organize files   │                          │ → Animated rings visualization
└─────────────────┘                          │

Phase 3: Best Picks                           │
┌─────────────────┐     ← event ──────────── │ Event: { type: "phase_start",
│ For each cluster:│                          │          phase: "best_picks" }
│   Pick highest   │                          │
│   quality image  │                          │
│ Copy to          │                          │
│   best_picks/    │                          │
└─────────────────┘     ← event ──────────── │ Event: { type: "pipeline_complete",
                                              │   summary: { total: 79, good: 45,
Save all results to DB                        │     blurry: 20, clusters: 8, ... } }
                                              │
                                              │ → loadResults(sessionId)
                                              │ → navigate('/results')
```

### 6.5 Viewing Results

```
ResultsPage mounts
  → loadResults(sessionId)
  → GET /api/sessions/abc-123/results
  → Backend reads JSON from SQLite, returns:
    {
      quality_results: [{ filename, category, score, ... }, ...],  // 79 items
      clusters: { "0": [...], "1": [...], ... },                   // 8 groups
      cluster_assignments: [{ filename, cluster_id }, ...],
      best_picks: [{ filename, cluster_id, score, reason }, ...],
      summary: { total: 79, good: 45, blurry: 20, ... }
    }

Tab: Quality
  → QualityOverview renders grid of ImageCard components
  → Each <img src="/api/sessions/abc-123/images/IMG_001.jpg?size=thumb">
  → Backend generates 200px thumbnail, caches it, returns JPEG

Tab: Clusters
  → ClusterView shows expandable group cards
  → User clicks to expand → sees horizontal scroll of thumbnails
  → Click an image to override the best pick selection
    → PUT /api/sessions/abc-123/overrides
      Body: { overrides: { "0": "IMG_005.jpg" } }

Tab: Best Picks
  → BestPicksGrid shows the selected best images
  → Click any image → Lightbox opens (full-size view + metrics panel)
```

### 6.6 How Images Display Without Uploading

This is one of the most important concepts:

```
Traditional web app:                    This app (local-first):
─────────────────────                   ────────────────────────

User uploads image                      User selects a folder path
  → Sent over network to server           → Only the PATH string is sent
  → Stored on server's disk               → "C:\\Photos"
  → Served back as URL                    → Backend reads from YOUR disk

Browser:                                Browser:
<img src="https://server/upload/123">   <img src="/api/sessions/abc/images/photo.jpg">
  ↓                                       ↓
  Network request to remote server        Vite proxy → localhost:8000
  ↓                                       ↓
  Remote server reads from its disk       LOCAL server reads from YOUR disk
  ↓                                       ↓
  Sends image bytes over internet         Sends image bytes over localhost
  ↓                                       ↓
  Browser renders                         Browser renders

Speed: ~200ms (network latency)         Speed: ~5ms (disk read, no network)
```

**The magic is the Vite proxy** (see next section) and the fact that both the
frontend and backend run on the same machine.

---

## 7. The Vite Dev Proxy — Why It All Works Locally

**`vite.config.ts`:**
```ts
export default defineConfig({
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        ws: true,  // Also proxy WebSocket connections
      },
    },
  },
})
```

**What this does:**

```
Browser requests:  localhost:5173/api/sessions
Vite intercepts:   "starts with /api → forward to localhost:8000"
Actual request:    localhost:8000/api/sessions
Response flows:    FastAPI → Vite proxy → Browser

Browser requests:  localhost:5173/dashboard  (or any non-/api path)
Vite serves:       React app (index.html + JavaScript)
```

**Why it's needed:**
- The browser runs at `localhost:5173` (Vite dev server)
- The backend runs at `localhost:8000` (FastAPI)
- Without the proxy, browser requests to `/api/...` would go to Vite (404)
- The proxy transparently forwards `/api/*` to FastAPI
- This also handles WebSocket upgrades (`ws: true`) for real-time progress

**In production**, the built frontend (`frontend/dist/`) is served by FastAPI itself,
so no proxy is needed.

---

## 8. Key Techniques Explained

### Lazy Loading (Code Splitting)
```tsx
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
```
Instead of bundling ALL pages into one large JavaScript file, Vite creates
separate chunks. The Dashboard chunk only downloads when you navigate there.
This makes the initial page load (hero) much faster.

### Zustand Store Pattern
```ts
// Create store
const useStore = create((set) => ({
  count: 0,
  increment: () => set((s) => ({ count: s.count + 1 })),
}))

// Use in ANY component (no Provider needed)
function Counter() {
  const count = useStore((s) => s.count)       // Only re-renders when count changes
  const increment = useStore((s) => s.increment)
  return <button onClick={increment}>{count}</button>
}
```

### ProcessPoolExecutor (Parallel Processing)
```python
with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(analyze_image, path) for path in images]
    for future in as_completed(futures):
        result = future.result()
        progress_queue.put({"type": "progress", "image": result})
```
This runs image analysis across multiple CPU cores simultaneously.
4 workers = 4 images analyzed at the same time.

### WebSocket vs HTTP Polling
```
HTTP Polling (bad):                WebSocket (what we use):
──────────────────                 ────────────────────────
Every 500ms:                       One connection, stays open:
  GET /progress → { current: 5 }    Server pushes: { current: 5 }
  GET /progress → { current: 5 }    Server pushes: { current: 6 }
  GET /progress → { current: 6 }    Server pushes: { current: 7 }
  GET /progress → { current: 6 }    ...
  GET /progress → { current: 7 }
                                   Real-time, no wasted requests
  Wasteful, delayed updates
```

### Thumbnail Caching
```python
# First request: generate + cache (50ms)
cache_key = md5("C:\\Photos\\IMG_001.jpg:200")  →  "a1b2c3d4.jpg"
# Save to: ~/.order-block/thumbnails/a1b2c3d4.jpg

# Second request: serve from cache (1ms)
if cached_path.exists():
    return cached_path  # instant!
```

### CSS Custom Properties for Theming
```css
/* Light (default) */
:root { --color-background: #FAFAFA; }

/* Dark (when .dark class is on <html>) */
.dark { --color-background: #0a0a0b; }
```
One toggle changes ALL colors across the entire app instantly.

---

## 9. Technology Reference

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **UI Framework** | React 19 | Component-based UI |
| **Language** | TypeScript 5.9 | Type safety for JS |
| **Build Tool** | Vite 7 | Fast dev server + bundler |
| **Routing** | React Router 7 | Client-side page navigation |
| **State** | Zustand 5 | Global state management |
| **Animation** | Framer Motion 12 | Page transitions + hero animation |
| **Styling** | Tailwind CSS 4 | Utility-first CSS |
| **Icons** | Lucide React | SVG icon library |
| **Backend** | FastAPI | Python web framework |
| **Server** | Uvicorn | ASGI server for FastAPI |
| **Database** | SQLAlchemy + SQLite | Session persistence |
| **Validation** | Pydantic 2 | Request/response schemas |
| **Real-time** | WebSockets | Live progress streaming |
| **Image Analysis** | OpenCV | Blur, exposure, noise detection |
| **Image I/O** | Pillow | Thumbnails, format support |
| **Math** | NumPy | Array operations for metrics |
| **AI Embeddings** | CLIP (PyTorch) | Visual similarity (optional) |
| **Clustering** | scikit-learn | DBSCAN grouping |
| **Hashing** | imagehash | Fast perceptual similarity |
| **Parallel** | ProcessPoolExecutor | Multi-core image processing |

---

*This documentation covers the complete architecture of Order Block.
Every HTTP request, WebSocket message, database query, image processing step,
and UI interaction is explained above.*
