import { X } from 'lucide-react'

interface StateSelectionBannerProps {
  stateName: string | null
  onClear: () => void
}

export function StateSelectionBanner({ stateName, onClear }: StateSelectionBannerProps) {
  if (!stateName) return null

  return (
    <div className="selection-banner" role="status">
      <span><strong>{stateName}</strong> selected — related views are highlighted.</span>
      <button type="button" className="button button--quiet" onClick={onClear} aria-label="Clear selected state">
        <X size={15} aria-hidden="true" /> Clear selection
      </button>
    </div>
  )
}
