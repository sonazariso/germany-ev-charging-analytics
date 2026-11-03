import type { DashboardData, GeoJsonFeatureCollection } from './types'

export async function loadDashboardData() {
  const [dashboardResponse, geoResponse] = await Promise.all([
    fetch('/data/dashboard.json'),
    fetch('/data/germany-states.geo.json'),
  ])

  if (!dashboardResponse.ok) throw new Error(`Could not load dashboard data (${dashboardResponse.status})`)
  if (!geoResponse.ok) throw new Error(`Could not load map geometry (${geoResponse.status})`)

  const [dashboard, geoJson] = (await Promise.all([
    dashboardResponse.json(),
    geoResponse.json(),
  ])) as [DashboardData, GeoJsonFeatureCollection]

  return { dashboard, geoJson }
}
