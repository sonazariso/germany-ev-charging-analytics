import { useMemo, useState } from 'react'
import { Activity, Car, Gauge, Plug, Wrench, Zap } from 'lucide-react'
import { ChartCard } from '../components/ChartCard'
import { EChart } from '../components/EChart'
import { KpiCard } from '../components/KpiCard'
import { SourceDates } from '../components/SourceDates'
import { formatCount, formatDateLabel, formatExactDate, formatOneDecimal, formatPercent } from '../data/format'
import { colors, chartTextStyle, powerBandColors } from '../data/theme'
import type { DashboardData } from '../data/types'

interface NationalSummaryProps {
  data: DashboardData
}

const axisLabel = { color: colors.axis, fontSize: 11 }
const splitLine = { lineStyle: { color: colors.grid, width: 1 } }

function HistoryTooltip(params: unknown) {
  const points = Array.isArray(params) ? params as Array<Record<string, unknown>> : []
  if (points.length === 0) return ''
  const date = typeof points[0].axisValue === 'string' ? points[0].axisValue : ''
  return [
    `<div class="tooltip-date">${formatExactDate(date)}</div>`,
    ...points.map((point) => `<div class="tooltip-row"><span>${String(point.seriesName)}</span><strong>${formatCount(Number(point.value))}</strong></div>`),
  ].join('')
}

export function NationalSummary({ data }: NationalSummaryProps) {
  const [selectedBand, setSelectedBand] = useState<string | null>(null)
  const julyHistory = data.history.find((row) => row.stockDate === data.meta.sourceDates.kba) ?? data.history[data.history.length - 1]

  const mixOption = useMemo(() => ({
    animationDuration: 350,
    textStyle: chartTextStyle,
    tooltip: {
      trigger: 'item',
      backgroundColor: colors.navy,
      borderWidth: 0,
      textStyle: { color: '#FFFFFF' },
      formatter: (params: Record<string, unknown>) => {
        const name = String(params.name ?? '')
        const band = data.powerBands.find((item) => item.name === name)
        return band ? `<div class="tooltip-date">${name}</div><div class="tooltip-row"><span>Points</span><strong>${formatCount(band.chargingPointCount)}</strong></div><div class="tooltip-row"><span>Share</span><strong>${formatPercent(band.chargingPointSharePct, 1)}</strong></div>` : name
      },
    },
    legend: {
      bottom: 0,
      left: 'center',
      selectedMode: 'single',
      itemWidth: 10,
      itemHeight: 10,
      textStyle: { color: colors.muted, fontSize: 11 },
      selected: Object.fromEntries(data.powerBands.map((band) => [band.name, selectedBand === null || selectedBand === band.name])),
    },
    graphic: [
      {
        type: 'group',
        left: 'center',
        top: 'middle',
        children: [
          { type: 'text', top: -18, style: { text: formatCount(data.national.chargingPointCount), fill: colors.navy, fontSize: 23, fontWeight: 750, textAlign: 'center' } },
          { type: 'text', top: 16, style: { text: 'Total points', fill: colors.muted, fontSize: 11, textAlign: 'center' } },
        ],
      },
    ],
    series: [
      {
        name: 'Charging points',
        type: 'pie',
        radius: ['53%', '76%'],
        center: ['50%', '45%'],
        selectedMode: 'single',
        selectedOffset: 5,
        avoidLabelOverlap: true,
        label: { show: false },
        labelLine: { show: false },
        itemStyle: { borderColor: colors.panel, borderWidth: 3 },
        emphasis: { scale: true, scaleSize: 4 },
        data: data.powerBands.map((band) => ({
          name: band.name,
          value: band.chargingPointCount,
          selected: selectedBand === band.name,
          itemStyle: { color: powerBandColors[band.name] ?? colors.blue, opacity: selectedBand === null || selectedBand === band.name ? 1 : 0.38 },
        })),
      },
    ],
  }), [data, selectedBand])

  const historyOption = useMemo(() => ({
    animationDuration: 450,
    textStyle: chartTextStyle,
    color: [colors.navyAccent, colors.gold],
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: colors.axis, type: 'dashed' } },
      backgroundColor: colors.navy,
      borderWidth: 0,
      textStyle: { color: '#FFFFFF' },
      formatter: HistoryTooltip,
    },
    legend: { top: 0, right: 0, itemWidth: 12, itemHeight: 8, textStyle: { color: colors.muted, fontSize: 11 } },
    grid: { left: 54, right: 124, top: 38, bottom: 42 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.history.map((row) => row.stockDate),
      axisLine: { lineStyle: { color: colors.grid } },
      axisTick: { show: false },
      axisLabel: { ...axisLabel, formatter: (value: string) => formatDateLabel(value) },
    },
    yAxis: {
      type: 'value',
      min: 0,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { ...axisLabel, formatter: (value: number) => `${Math.round(value / 1000000)}m` },
      splitLine,
    },
    series: [
      {
        name: 'BEV',
        type: 'line',
        smooth: 0.2,
        showSymbol: false,
        lineStyle: { width: 2.5 },
        endLabel: { show: true, formatter: (params: Record<string, unknown>) => `BEV ${formatCount(Number(params.value))}`, color: colors.navyAccent, fontSize: 11, fontWeight: 700 },
        data: data.history.map((row) => row.bevStock),
      },
      {
        name: 'PHEV',
        type: 'line',
        smooth: 0.2,
        showSymbol: false,
        lineStyle: { width: 2.5 },
        endLabel: { show: true, formatter: (params: Record<string, unknown>) => `PHEV ${formatCount(Number(params.value))}`, color: colors.gold, fontSize: 11, fontWeight: 700 },
        data: data.history.map((row) => row.phevStock),
      },
    ],
  }), [data])

  const powerOption = useMemo(() => ({
    animationDuration: 300,
    textStyle: chartTextStyle,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: colors.navy,
      borderWidth: 0,
      textStyle: { color: '#FFFFFF' },
      formatter: (params: unknown) => {
        const point = Array.isArray(params) ? params[0] as Record<string, unknown> : params as Record<string, unknown>
        const band = data.powerBands.find((item) => item.name === String(point?.name ?? ''))
        return band ? `<div class="tooltip-date">${band.name}</div><div class="tooltip-row"><span>Points</span><strong>${formatCount(band.chargingPointCount)}</strong></div><div class="tooltip-row"><span>Share</span><strong>${formatPercent(band.chargingPointSharePct, 1)}</strong></div>` : ''
      },
    },
    grid: { left: 220, right: 84, top: 16, bottom: 34 },
    xAxis: { type: 'value', min: 0, axisLine: { lineStyle: { color: colors.grid } }, axisTick: { show: false }, axisLabel, splitLine },
    yAxis: { type: 'category', inverse: true, data: data.powerBands.map((band) => band.name), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { ...axisLabel, width: 210, overflow: 'break' } },
    series: [{
      type: 'bar',
      barWidth: 18,
      data: data.powerBands.map((band) => ({
        name: band.name,
        value: band.chargingPointCount,
        itemStyle: { color: powerBandColors[band.name] ?? colors.blue, borderRadius: [0, 4, 4, 0], opacity: selectedBand === null || selectedBand === band.name ? 1 : 0.35 },
      })),
      label: { show: true, position: 'right', color: colors.navy, fontSize: 11, formatter: (params: Record<string, unknown>) => formatCount(Number(params.value)) },
      emphasis: { focus: 'series' },
    }],
  }), [data, selectedBand])

  const statusOption = useMemo(() => ({
    animationDuration: 300,
    textStyle: chartTextStyle,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: colors.navy,
      borderWidth: 0,
      textStyle: { color: '#FFFFFF' },
      formatter: (params: unknown) => {
        const point = Array.isArray(params) ? params[0] as Record<string, unknown> : params as Record<string, unknown>
        const status = data.equipmentStatus.find((item) => item.name === String(point?.name ?? ''))
        return status ? `<div class="tooltip-date">${status.name}</div><div class="tooltip-row"><span>Equipment</span><strong>${formatCount(status.equipmentCount)}</strong></div><div class="tooltip-row"><span>Share</span><strong>${formatPercent(status.equipmentSharePct, 2)}</strong></div>` : ''
      },
    },
    grid: { left: 92, right: 120, top: 16, bottom: 34 },
    xAxis: { type: 'value', min: 0, max: 120000, axisLine: { lineStyle: { color: colors.grid } }, axisTick: { show: false }, axisLabel, splitLine },
    yAxis: { type: 'category', inverse: true, data: data.equipmentStatus.map((status) => status.name), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { ...axisLabel, fontSize: 11 } },
    series: [{
      type: 'bar',
      barWidth: 22,
      data: data.equipmentStatus.map((status) => ({ name: status.name, value: status.equipmentCount, itemStyle: { color: status.name === 'In Wartung' ? colors.gold : colors.teal, borderRadius: [0, 4, 4, 0] } })),
      label: { show: true, position: 'right', color: colors.navy, fontSize: 11, formatter: (params: Record<string, unknown>) => formatCount(Number(params.value)) },
    }],
  }), [data])

  const selectBand = (params: Record<string, unknown>) => {
    const bandName = typeof params.name === 'string' ? params.name : null
    setSelectedBand((current) => bandName && current === bandName ? null : bandName)
  }

  return (
    <div className="page page--national">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Executive Overview · National Summary</p>
          <h1>Germany EV Charging Analytics</h1>
          <p className="page-heading__lede">A validated view of the published public-charging register and registered electric-vehicle stock.</p>
        </div>
        <SourceDates bnetza={data.meta.sourceDates.bnetza} kba={data.meta.sourceDates.kba} />
      </div>

      <section className="kpi-grid kpi-grid--five" aria-label="National key performance indicators">
        <KpiCard label="Charging equipment" value={formatCount(data.national.equipmentCount)} detail="Published equipment records" icon={Plug} tone="navy" />
        <KpiCard label="Charging points" value={formatCount(data.national.chargingPointCount)} detail="Populated point slots" icon={Zap} tone="teal" />
        <KpiCard label="Fast charging points" value={formatCount(data.national.fastChargingPointCount)} detail={`${formatPercent(data.national.fastPointSharePct, 1)} of point slots · >22 kW`} icon={Gauge} tone="blue" />
        <KpiCard label="BEV stock" value={formatCount(julyHistory.bevStock)} detail="KBA registered passenger cars" icon={Car} tone="navy" supplementary={`PHEV stock · ${formatCount(julyHistory.phevStock)}`} />
        <KpiCard label="Declared nominal power" value={`${formatOneDecimal(data.national.equipmentNominalPowerMw)} MW`} detail="Equipment-level declared power" icon={Activity} tone="gold" />
      </section>

      <div className="dashboard-grid dashboard-grid--national-main">
        <ChartCard
          title="Charging Point Mix"
          subtitle="Mutually exclusive bands · click a segment or legend to highlight"
          className="chart-card--mix"
          actions={selectedBand ? <button type="button" className="button button--quiet" onClick={() => setSelectedBand(null)}>Clear band</button> : undefined}
          note="Bands use the maximum parsed declared power per point; they total exactly 211,253 point slots."
        >
          <EChart option={mixOption} height={300} ariaLabel="Donut chart of four mutually exclusive charging power bands" onEvents={{ click: selectBand }} />
        </ChartCard>

        <ChartCard
          title="National EV Stock History"
          subtitle="33 validated KBA observations · registered passenger-car stock"
          className="chart-card--history"
          note={`Latest observation: ${formatDateLabel(julyHistory.stockDate)} · BEV ${formatCount(julyHistory.bevStock)} · PHEV ${formatCount(julyHistory.phevStock)}`}
        >
          <EChart option={historyOption} height={300} ariaLabel="Line chart showing national BEV and PHEV stock across 33 KBA observations" />
        </ChartCard>
      </div>

      <div className="dashboard-grid dashboard-grid--national-bottom">
        <ChartCard
          title="Power Band Distribution"
          subtitle="Absolute point-slot count · zero baseline"
          actions={selectedBand ? <span className="active-filter"><span className="active-filter__dot" /> {selectedBand}</span> : undefined}
        >
          <EChart option={powerOption} height={225} ariaLabel="Horizontal bar chart of charging point counts by power band" onEvents={{ click: selectBand }} />
        </ChartCard>

        <ChartCard title="Equipment Status" subtitle="Published snapshot status · zero baseline" note="The 20 In Wartung records remain visible; status is a snapshot label, not uptime. ">
          <EChart option={statusOption} height={225} ariaLabel="Horizontal bar chart of operating and maintenance equipment status" />
        </ChartCard>
      </div>

      <section className="methodology-note" aria-label="Methodology note">
        <Wrench size={16} aria-hidden="true" />
        <p>Infrastructure is the BNetzA published register snapshot dated <strong>30 September 2026</strong>; vehicle stock is KBA registered passenger-car stock dated <strong>1 July 2026</strong>. Charging-point bands use the maximum parsed declared power per point. Equipment and populated point slots are distinct measures. National KBA totals include <strong>Sonstige</strong>; the state view uses only the 16 named Bundesländer. Counts do not measure utilization, demand, availability, or infrastructure adequacy.</p>
      </section>
    </div>
  )
}
