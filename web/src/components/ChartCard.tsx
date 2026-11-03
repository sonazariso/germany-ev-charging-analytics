import type { ReactNode } from 'react'
import { Info } from 'lucide-react'

interface ChartCardProps {
  title: string
  subtitle?: string
  children: ReactNode
  className?: string
  actions?: ReactNode
  note?: string
}

export function ChartCard({ title, subtitle, children, className = '', actions, note }: ChartCardProps) {
  return (
    <section className={`chart-card ${className}`}>
      <div className="chart-card__header">
        <div>
          <h2>{title}</h2>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {actions && <div className="chart-card__actions">{actions}</div>}
      </div>
      <div className="chart-card__body">{children}</div>
      {note && (
        <div className="chart-card__note">
          <Info size={14} aria-hidden="true" />
          <span>{note}</span>
        </div>
      )}
    </section>
  )
}
