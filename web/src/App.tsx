import { useEffect, useState } from 'react'
import { BarChart3, ChevronRight, CircleAlert, Database, MapPinned } from 'lucide-react'
import { loadDashboardData } from './data/loadData'
import type { DashboardData, GeoJsonFeatureCollection } from './data/types'
import { GeographicView } from './pages/GeographicView'
import { NationalSummary } from './pages/NationalSummary'

type Page = 'national' | 'geographic'

function pageFromHash() : Page {
  return window.location.hash === '#geographic' ? 'geographic' : 'national'
}

export default function App() {
  const [page, setPage] = useState<Page>(() => pageFromHash())
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [geoJson, setGeoJson] = useState<GeoJsonFeatureCollection | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleHashChange = () => setPage(pageFromHash())
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  useEffect(() => {
    let cancelled = false
    loadDashboardData()
      .then(({ dashboard: loadedDashboard, geoJson: loadedGeoJson }) => {
        if (cancelled) return
        setDashboard(loadedDashboard)
        setGeoJson(loadedGeoJson)
      })
      .catch((loadError: unknown) => {
        if (cancelled) return
        setError(loadError instanceof Error ? loadError.message : 'The dashboard data could not be loaded.')
      })
    return () => { cancelled = true }
  }, [])

  const navigate = (nextPage: Page) => {
    window.location.hash = nextPage
    setPage(nextPage)
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__inner">
          <button type="button" className="brand" onClick={() => navigate('national')} aria-label="Go to National Summary">
            <span className="brand__mark"><ZapMark /></span>
            <span className="brand__copy"><strong>Germany EV</strong><small>Charging Analytics</small></span>
          </button>
          <nav className="primary-nav" aria-label="Dashboard pages">
            <button type="button" className={`nav-button ${page === 'national' ? 'is-active' : ''}`} onClick={() => navigate('national')} aria-current={page === 'national' ? 'page' : undefined}><BarChart3 size={16} aria-hidden="true" /> National Summary</button>
            <button type="button" className={`nav-button ${page === 'geographic' ? 'is-active' : ''}`} onClick={() => navigate('geographic')} aria-current={page === 'geographic' ? 'page' : undefined}><MapPinned size={16} aria-hidden="true" /> Geographic View</button>
          </nav>
          <div className="topbar__status"><Database size={14} aria-hidden="true" /> Validated local extracts <ChevronRight size={13} aria-hidden="true" /></div>
        </div>
      </header>

      <main className="app-main">
        {error ? (
          <section className="load-error" role="alert">
            <CircleAlert size={22} aria-hidden="true" />
            <div><h1>Dashboard data unavailable</h1><p>{error}</p><p>Run <code>npm run prepare:data</code> from the <code>web/</code> directory, then reload.</p></div>
          </section>
        ) : !dashboard || !geoJson ? (
          <div className="loading-state" role="status"><span className="loading-state__spinner" /> Loading validated dashboard data…</div>
        ) : page === 'national' ? (
          <NationalSummary data={dashboard} />
        ) : (
          <GeographicView data={dashboard} geoJson={geoJson} />
        )}
      </main>

      <footer className="app-footer">
        <span>Batch 23 web dashboard · {dashboard?.meta.preparationVersion ?? 'loading'}</span>
        <span>Local assets · no external map API</span>
      </footer>
    </div>
  )
}

function ZapMark() {
  return <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z" /></svg>
}
