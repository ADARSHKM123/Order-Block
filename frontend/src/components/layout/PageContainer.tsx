import type { ReactNode } from 'react'
import { motion } from 'framer-motion'

interface Props {
  title: string
  subtitle?: string
  actions?: ReactNode
  children: ReactNode
}

const pageVariants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
}

export function PageContainer({ title, subtitle, actions, children }: Props) {
  return (
    <div className="flex-1 overflow-auto bg-background">
      <motion.div
        variants={pageVariants}
        initial="initial"
        animate="animate"
        exit="exit"
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
        className="max-w-7xl mx-auto px-8 py-10"
      >
        <div className="flex items-start justify-between mb-10">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-text-primary">
              {title}
            </h1>
            {subtitle && (
              <p className="text-text-secondary mt-1.5 text-[15px]">{subtitle}</p>
            )}
          </div>
          {actions && <div className="flex gap-2">{actions}</div>}
        </div>
        {children}
      </motion.div>
    </div>
  )
}
