import { useEffect, useRef } from 'react'
import * as echarts from 'echarts/core'
import { BarChart, LineChart, MapChart, PieChart } from 'echarts/charts'
import {
  AriaComponent,
  DataZoomComponent,
  GraphicComponent,
  GeoComponent,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart,
  LineChart,
  MapChart,
  PieChart,
  AriaComponent,
  DataZoomComponent,
  GraphicComponent,
  GeoComponent,
  GridComponent,
  LegendComponent,
  TitleComponent,
  TooltipComponent,
  VisualMapComponent,
  CanvasRenderer,
])

type ChartEvent = (params: Record<string, unknown>) => void

interface EChartProps {
  option: Record<string, unknown>
  height?: number | string
  className?: string
  ariaLabel: string
  onEvents?: Record<string, ChartEvent>
}

export function EChart({ option, height = 300, className = '', ariaLabel, onEvents = {} }: EChartProps) {
  const chartRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!chartRef.current) return undefined
    const existingChart = echarts.getInstanceByDom(chartRef.current)
    existingChart?.dispose()
    const chart = echarts.init(chartRef.current, undefined, { renderer: 'canvas' })
    chart.setOption(option, true)
    Object.entries(onEvents).forEach(([eventName, handler]) => chart.on(eventName, handler as unknown as (...args: unknown[]) => boolean | void))

    const resizeObserver = new ResizeObserver(() => chart.resize())
    resizeObserver.observe(chartRef.current)

    return () => {
      resizeObserver.disconnect()
      chart.dispose()
    }
  }, [onEvents, option])

  return <div ref={chartRef} className={`echart ${className}`} style={{ height }} role="img" aria-label={ariaLabel} />
}

export { echarts }
