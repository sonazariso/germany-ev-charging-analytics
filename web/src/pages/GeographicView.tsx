import { useMemo, useState, type CSSProperties, type KeyboardEvent } from 'react'
import { ArrowDownWideNarrow, ArrowUpWideNarrow, Building2, Map, RotateCcw, Table2, TrendingUp, Zap } from 'lucide-react'
import { ChartCard } from '../components/ChartCard'
import { EChart, echarts } from '../components/EChart'
import { SourceDates } from '../components/SourceDates'
import { StateSelectionBanner } from '../components/StateSelectionBanner'
import { formatCount, formatPercent } from '../data/format'
import { colors, chartTextStyle } from '../data/theme'
import type { DashboardData, GeoJsonFeatureCollection, StateComparison, StateCharging } from '../data/types'

interface GeographicViewProps {
  data: DashboardData
  geoJson: GeoJsonFeatureCollection
}

type SortKey = 'bevPassengerCarStock' | 'chargingPointCount' | 'fastPointSharePct' | 'bevPenetrationPct'

const sortOptions: Array<{ value: SortKey; label: string }> = [
  { value: 'bevPenetrationPct', label: 'BEV penetration' },
  { value: 'bevPassengerCarStock', label: 'BEV stock' },
  { value: 'chargingPointCount', label: 'Charging points' },
  { value: 'fastPointSharePct', label: 'Fast-point share' },
]

function maximumBy<T>(rows: T[], selector: (row: T) => number) {
  return rows.reduce((best, row) => selector(row) > selector(best) ? row : best, rows[0])
}

function getStateComparison(data: DashboardData, stateName: string) {
  return data.stateComparison.find((row) => row.stateName === stateName)
}

function mapTooltip(params: Record<string, unknown>, data: DashboardData) {
  const stateName = String(params.name ?? '')
  const charging = data.stateCharging.find((row) => row.stateName === stateName)
  const comparison = getStateComparison(data, stateName)
  if (!charging || !comparison) return stateName
  return `<div class="tooltip-date">${stateName}</div><div class="tooltip-row"><span>Charging points</span><strong>${formatCount(charging.chargingPointCount)}</strong></div><div class="tooltip-row"><span>Fast share</span><strong>${formatPercent(charging.fastPointSharePct, 2)}</strong></div><div class="tooltip-row"><span>BEV penetration</span><strong>${formatPercent(comparison.bevPenetrationPct, 2)}</strong></div>`
}

function buildMapOption(data: DashboardData, selectedState: string | null) {
  const min = Math.min(...data.stateCharging.map((row) => row.chargingPointCount))
  const max = Math.max(...data.stateCharging.map((row) => row.chargingPointCount))
  return {
    animationDuration: 450,
    textStyle: chartTextStyle,
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.navy,
      borderWidth: 0,
      textStyle: { color: '#FFFFFF' },
      formatter: (params: Record<string, unknown>) => mapTooltip(params, data),
    },
    visualMap: {
      min,
      max,
      left: 'center',
      bottom: 4,
      orient: 'horizontal',
      calculable: false,
      itemWidth: 120,
      itemHeight: 8,
      text: ['More points', 'Fewer points'],
      textStyle: { color: colors.muted, fontSize: 10 },
      inRange: { color: ['#D5E3E7', '#81C2C1', colors.teal, colors.navyAccent] },
    },
    series: [{
      name: 'Charging points',
      type: 'map',
      map: 'germany',
      roam: false,
      selectedMode: 'single',
      zoom: 1.05,
      layoutCenter: ['50%', '45%'],
      layoutSize: '93%',
      label: { show: false },
      itemStyle: { borderColor: '#FFFFFF', borderWidth: 1.2 },
      emphasis: { label: { show: true, color: colors.navy, fontSize: 10, fontWeight: 700 }, itemStyle: { areaColor: '#8CCBC8', borderColor: colors.navy, borderWidth: 1.6 } },
      select: { itemStyle: { areaColor: colors.selected, borderColor: colors.navy, borderWidth: 2 }, label: { show: true, color: '#FFFFFF', fontSize: 10, fontWeight: 700 } },
      data: data.stateCharging.map((row) => ({
        name: row.stateName,
        value: row.chargingPointCount,
        selected: selectedState === row.stateName,
      })),
    }],
  }
}

function buildRankingOption(rows: StateCharging[], selectedState: string | null) {
  const topRows = [...rows].sort((a, b) => b.chargingPointCount - a.chargingPointCount).slice(0, 10).reverse()
  return {
    animationDuration: 350,
    textStyle: chartTextStyle,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: colors.navy,
      borderWidth: 0,
      textStyle: { color: '#FFFFFF' },
      formatter: (params: unknown) => {
        const point = Array.isArray(params) ? params[0] as Record<string, unknown> : params as Record<string, unknown>
        const row = rows.find((item) => item.stateName === String(point?.name ?? ''))
        return row ? `<div class="tooltip-date">${row.stateName}</div><div class="tooltip-row"><span>Charging points</span><strong>${formatCount(row.chargingPointCount)}</strong></div><div class="tooltip-row"><span>Fast share</span><strong>${formatPercent(row.fastPointSharePct, 2)}</strong></div>` : ''
      },
    },
    grid: { left: 155, right: 54, top: 12, bottom: 24 },
    xAxis: { type: 'value', min: 0, axisLine: { lineStyle: { color: colors.grid } }, axisTick: { show: false }, axisLabel: { color: colors.axis, fontSize: 10 }, splitLine: { lineStyle: { color: colors.grid } } },
    yAxis: { type: 'category', inverse: false, data: topRows.map((row) => row.stateName), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: colors.muted, fontSize: 10, width: 145, overflow: 'truncate' } },
    series: [{
      type: 'bar',
      barWidth: 14,
      data: topRows.map((row) => ({ name: row.stateName, value: row.chargingPointCount, itemStyle: { color: row.stateName === selectedState ? colors.selected : colors.teal, borderRadius: [0, 4, 4, 0] } })),
      label: { show: true, position: 'right', color: colors.navy, fontSize: 10, formatter: (params: Record<string, unknown>) => formatCount(Number(params.value)) },
    }],
  }
}

function buildPenetrationOption(rows: StateComparison[], selectedState: string | null) {
  const sortedRows = [...rows].sort((a, b) => b.bevPenetrationPct - a.bevPenetrationPct)
  return {
    animationDuration: 350,
    textStyle: chartTextStyle,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: colors.navy,
      borderWidth: 0,
      textStyle: { color: '#FFFFFF' },
      formatter: (params: unknown) => {
        const point = Array.isArray(params) ? params[0] as Record<string, unknown> : params as Record<string, unknown>
        return `<div class="tooltip-date">${String(point?.name ?? '')}</div><div class="tooltip-row"><span>BEV penetration</span><strong>${formatPercent(Number(point?.value), 2)}</strong></div>`
      },
    },
    grid: { left: 154, right: 48, top: 12, bottom: 24 },
    xAxis: { type: 'value', min: 0, max: 7, axisLine: { lineStyle: { color: colors.grid } }, axisTick: { show: false }, axisLabel: { color: colors.axis, fontSize: 10, formatter: (value: number) => `${value}%` }, splitLine: { lineStyle: { color: colors.grid } } },
    yAxis: { type: 'category', inverse: true, data: sortedRows.map((row) => row.stateName), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: colors.muted, fontSize: 10, width: 145, overflow: 'truncate' } },
    series: [{
      type: 'bar',
      barWidth: 13,
      data: sortedRows.map((row) => ({ name: row.stateName, value: row.bevPenetrationPct, itemStyle: { color: row.stateName === selectedState ? colors.selected : colors.navyAccent, borderRadius: [0, 4, 4, 0] } })),
      label: { show: true, position: 'right', color: colors.navy, fontSize: 10, formatter: (params: Record<string, unknown>) => formatPercent(Number(params.value), 2) },
    }],
  }
}

function TableCellBar({ value, max, children }: { value: number; max: number; children: string }) {
  const width = max > 0 ? Math.max(3, Math.min(100, (value / max) * 100)) : 0
  return <span className="table-bar" style={{ '--bar-width': `${width}%` } as CSSProperties}><span className="table-bar__fill" aria-hidden="true" /><span className="table-bar__value">{children}</span></span>
}

export function GeographicView({ data, geoJson }: GeographicViewProps) {
  const [selectedState, setSelectedState] = useState<string | null>(null)
  const [sortKey, setSortKey] = useState<SortKey>('bevPenetrationPct')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc')

  echarts.registerMap('germany', geoJson as never)

  const mostCharging = maximumBy(data.stateCharging, (row) => row.chargingPointCount)
  const highestPenetration = maximumBy(data.stateComparison, (row) => row.bevPenetrationPct)
  const highestFastShare = maximumBy(data.stateCharging, (row) => row.fastPointSharePct)

  const mapOption = useMemo(() => buildMapOption(data, selectedState), [data, selectedState])
  const rankingOption = useMemo(() => buildRankingOption(data.stateCharging, selectedState), [data.stateCharging, selectedState])
  const penetrationOption = useMemo(() => buildPenetrationOption(data.stateComparison, selectedState), [data.stateComparison, selectedState])

  const tableRows = useMemo(() => [...data.stateComparison].sort((a, b) => {
    const left = a[sortKey]
    const right = b[sortKey]
    if (left === right) return a.stateName.localeCompare(b.stateName)
    return sortDirection === 'desc' ? right - left : left - right
  }), [data.stateComparison, sortDirection, sortKey])

  const comparisonMaxPoints = Math.max(...data.stateComparison.map((row) => row.chargingPointCount))
  const comparisonMaxBev = Math.max(...data.stateComparison.map((row) => row.bevPassengerCarStock))

  const selectStateFromParams = (params: Record<string, unknown>) => {
    const stateName = typeof params.name === 'string' ? params.name : null
    if (stateName && data.stateComparison.some((row) => row.stateName === stateName)) setSelectedState((current) => current === stateName ? null : stateName)
  }

  const toggleSortDirection = () => setSortDirection((direction) => direction === 'desc' ? 'asc' : 'desc')

  const handleRowKeyDown = (event: KeyboardEvent<HTMLTableRowElement>, stateName: string) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      setSelectedState((current) => current === stateName ? null : stateName)
    }
  }

  return (
    <div className="page page--geographic">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Executive Overview · Geographic View</p>
          <h1>Germany EV Charging Analytics</h1>
          <p className="page-heading__lede">Sixteen-state comparison of the published charging register and KBA electric-vehicle stock.</p>
        </div>
        <SourceDates bnetza={data.meta.sourceDates.bnetza} kba={data.meta.sourceDates.kba} />
      </div>

      <StateSelectionBanner stateName={selectedState} onClear={() => setSelectedState(null)} />

      <section className="highlight-grid" aria-label="Geographic highlights">
        <article className="highlight-card highlight-card--teal">
          <span className="highlight-card__icon"><Building2 size={18} aria-hidden="true" /></span>
          <span className="highlight-card__label">Federal states</span>
          <strong>{data.meta.validation.federalStates}</strong>
          <small>Validated state scope</small>
        </article>
        <article className="highlight-card highlight-card--navy">
          <span className="highlight-card__icon"><Map size={18} aria-hidden="true" /></span>
          <span className="highlight-card__label">Most charging points</span>
          <strong>{mostCharging.stateName}</strong>
          <small>{formatCount(mostCharging.chargingPointCount)} point slots</small>
        </article>
        <article className="highlight-card highlight-card--blue">
          <span className="highlight-card__icon"><TrendingUp size={18} aria-hidden="true" /></span>
          <span className="highlight-card__label">Highest BEV penetration</span>
          <strong>{highestPenetration.stateName}</strong>
          <small>{formatPercent(highestPenetration.bevPenetrationPct, 2)} of passenger cars</small>
        </article>
        <article className="highlight-card highlight-card--gold">
          <span className="highlight-card__icon"><Zap size={18} aria-hidden="true" /></span>
          <span className="highlight-card__label">Highest fast-point share</span>
          <strong>{highestFastShare.stateName}</strong>
          <small>{formatPercent(highestFastShare.fastPointSharePct, 2)} of point slots</small>
        </article>
      </section>

      <div className="dashboard-grid dashboard-grid--geo-main">
        <ChartCard title="Germany State Map" subtitle="Charging point count · click a state to highlight related views" className="chart-card--map" note="Local geometry: 16 Bundesländer; attribution and source license are documented below the map.">
          <EChart option={mapOption} height={410} ariaLabel="Interactive choropleth map of Germany's 16 federal states by charging point count" onEvents={{ click: selectStateFromParams }} />
          <p className="map-attribution"><a href="https://github.com/isellsoap/deutschlandGeoJSON" target="_blank" rel="noreferrer">DeutschlandGeoJSON</a> · GIS-DATA / DIVA-GIS · Unlicense</p>
        </ChartCard>
        <ChartCard title="Charging Point Ranking" subtitle="Top ten federal states · absolute point-slot count" className="chart-card--ranking" actions={<span className="chart-inline-label"><span className="legend-dot legend-dot--teal" /> Point slots</span>}>
          <EChart option={rankingOption} height={410} ariaLabel="Horizontal ranking of the ten German federal states with the most charging points" onEvents={{ click: selectStateFromParams }} />
        </ChartCard>
      </div>

      <div className="dashboard-grid dashboard-grid--geo-bottom">
        <ChartCard
          title="State Comparison"
          subtitle="KBA July 2026 stock · BNetzA September 2026 infrastructure"
          className="chart-card--table"
          actions={<div className="table-controls"><label htmlFor="state-sort">Sort by</label><select id="state-sort" value={sortKey} onChange={(event) => setSortKey(event.target.value as SortKey)}>{sortOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select><button type="button" className="icon-button" onClick={toggleSortDirection} aria-label={`Sort ${sortDirection === 'desc' ? 'ascending' : 'descending'}`} title="Toggle sort direction">{sortDirection === 'desc' ? <ArrowDownWideNarrow size={16} /> : <ArrowUpWideNarrow size={16} />}</button></div>}
          note="Fast share is fast point slots divided by charging point slots. Cross-source dates are not contemporaneous; no adequacy interpretation is implied."
        >
          <div className="table-wrap">
            <table className="comparison-table">
              <thead>
                <tr><th scope="col">State</th><th scope="col">BEV stock</th><th scope="col">Charging points</th><th scope="col">Fast share</th><th scope="col">BEV penetration</th></tr>
              </thead>
              <tbody>
                {tableRows.map((row) => (
                  <tr key={row.stateName} className={selectedState === row.stateName ? 'is-selected' : ''} tabIndex={0} onClick={() => setSelectedState((current) => current === row.stateName ? null : row.stateName)} onKeyDown={(event) => handleRowKeyDown(event, row.stateName)}>
                    <th scope="row"><span className="state-cell"><span className="state-cell__marker" />{row.stateName}</span></th>
                    <td><TableCellBar value={row.bevPassengerCarStock} max={comparisonMaxBev}>{formatCount(row.bevPassengerCarStock)}</TableCellBar></td>
                    <td><TableCellBar value={row.chargingPointCount} max={comparisonMaxPoints}>{formatCount(row.chargingPointCount)}</TableCellBar></td>
                    <td><span className="metric-emphasis">{formatPercent(row.fastPointSharePct, 2)}</span></td>
                    <td><span className="metric-emphasis metric-emphasis--navy">{formatPercent(row.bevPenetrationPct, 2)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="table-footnote"><Table2 size={14} aria-hidden="true" /> Click or focus a row, then press Enter or Space to select a state.</div>
        </ChartCard>

        <ChartCard title="BEV Penetration by State" subtitle="KBA registered stock · July 2026 · all 16 states" className="chart-card--penetration" actions={<span className="chart-inline-label"><span className="legend-dot legend-dot--navy" /> BEV share</span>}>
          <EChart option={penetrationOption} height={520} ariaLabel="Horizontal comparison of BEV penetration across all 16 German federal states" onEvents={{ click: selectStateFromParams }} />
        </ChartCard>
      </div>

      <section className="methodology-note methodology-note--geo" aria-label="Geographic methodology note">
        <RotateCcw size={16} aria-hidden="true" />
        <p><strong>Scope:</strong> the state comparison uses the 16 named Bundesländer only. National KBA <strong>Deutschland</strong> and residual <strong>Sonstige</strong> totals are kept separate; July national BEV stock is 2,365,047 versus 2,362,218 across the 16 states. Charging and vehicle dates are 91 days apart, so the views are descriptive cross-source comparisons.</p>
      </section>
    </div>
  )
}
