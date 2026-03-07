import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Sidebar } from './components/layout/Sidebar'
import { DashboardPage } from './pages/DashboardPage'
import { SettingsPage } from './pages/SettingsPage'
import { ProcessingPage } from './pages/ProcessingPage'
import { ResultsPage } from './pages/ResultsPage'
import { HeroPage } from './pages/HeroPage'

function AppLayout() {
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <Sidebar />
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="/processing" element={<ProcessingPage />} />
          <Route path="/results" element={<ResultsPage />} />
        </Routes>
      </AnimatePresence>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HeroPage />} />
      <Route path="/*" element={<AppLayout />} />
    </Routes>
  )
}
