import { CalendarDays } from 'lucide-react'

interface SourceDatesProps {
  bnetza: string
  kba?: string
  compact?: boolean
}

function prettyDate(isoDate: string) {
  return new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${isoDate}T00:00:00Z`))
}

export function SourceDates({ bnetza, kba, compact = false }: SourceDatesProps) {
  return (
    <div className={`source-dates ${compact ? 'source-dates--compact' : ''}`} aria-label="Source reference dates">
      <span className="source-date"><CalendarDays size={14} aria-hidden="true" /> BNetzA: {prettyDate(bnetza)}</span>
      {kba && <span className="source-date"><CalendarDays size={14} aria-hidden="true" /> KBA: {prettyDate(kba)}</span>}
    </div>
  )
}
