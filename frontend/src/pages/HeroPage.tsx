import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import IntroAnimation from "../components/ui/scroll-morph-hero"

export function HeroPage() {
    const navigate = useNavigate()
    const [exiting, setExiting] = useState(false)

    const handleGetStarted = useCallback(() => {
        setExiting(true)
        // Quick fade-out, then navigate
        setTimeout(() => navigate('/dashboard'), 300)
    }, [navigate])

    return (
        <motion.div
            className="w-full h-screen overflow-hidden relative"
            animate={{ opacity: exiting ? 0 : 1, scale: exiting ? 1.02 : 1 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        >
            <IntroAnimation onGetStarted={handleGetStarted} />
        </motion.div>
    )
}
