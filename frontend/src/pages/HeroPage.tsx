import { useNavigate } from 'react-router-dom'
import IntroAnimation from "../components/ui/scroll-morph-hero"

export function HeroPage() {
    const navigate = useNavigate()

    return (
        <div className="w-full h-screen overflow-hidden relative">
            <IntroAnimation onGetStarted={() => navigate('/dashboard')} />
        </div>
    )
}
