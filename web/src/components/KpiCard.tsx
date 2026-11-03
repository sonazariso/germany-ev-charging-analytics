import type { LucideIcon } from 'lucide-react'

interface KpiCardProps {
  label: string
  value: string
  detail: string
  icon: LucideIcon
  tone: 'navy' | 'teal' | 'blue' | 'gold'
  supplementary?: string
}

export function KpiCard({ label, value, detail, icon: Icon, tone, supplementary }: KpiCardProps) {
  return (
    <article className={`kpi-card kpi-card--${tone}`}>
      <div className="kpi-card__topline">
        <span className="kpi-card__label">{label}</span>
        <span className="kpi-card__icon" aria-hidden="true"><Icon size={18} strokeWidth={1.8} /></span>
      </div>
      <div className="kpi-card__value">{value}</div>
      <div className="kpi-card__detail">{detail}</div>
      {supplementary && <div className="kpi-card__supplementary">{supplementary}</div>}
    </article>
  )
}
