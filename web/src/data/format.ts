export const formatCount = (value: number | null | undefined) =>
  value === null || value === undefined ? '—' : new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)

export const formatOneDecimal = (value: number | null | undefined) =>
  value === null || value === undefined ? '—' : new Intl.NumberFormat('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(value)

export const formatPercent = (value: number | null | undefined, digits = 2) =>
  value === null || value === undefined
    ? '—'
    : `${new Intl.NumberFormat('en-US', { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)}%`

export const formatDateLabel = (isoDate: string) =>
  new Intl.DateTimeFormat('en-GB', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${isoDate}T00:00:00Z`))

export const formatExactDate = (isoDate: string) =>
  new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${isoDate}T00:00:00Z`))

export const compactCount = (value: number) =>
  new Intl.NumberFormat('en-US', { notation: 'compact', maximumFractionDigits: 1 }).format(value)
