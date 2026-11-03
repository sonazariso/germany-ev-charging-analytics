export const colors = {
  canvas: '#E8EEF1',
  panel: '#FFFFFF',
  navy: '#142B3A',
  navyAccent: '#163A5F',
  teal: '#1C9A9C',
  tealDeep: '#0A7073',
  blue: '#367A9E',
  gold: '#D6A84F',
  normal: '#C9D7DE',
  muted: '#6F7C83',
  axis: '#8997A0',
  grid: '#D9E1E5',
  border: '#E1E8EB',
  selected: '#0E7E83',
  danger: '#A34B46',
} as const

export const chartTextStyle = {
  color: colors.navy,
  fontFamily: 'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
} as const

export const powerBandColors: Record<string, string> = {
  'Normal ≤22 kW': colors.normal,
  'Fast >22 and <150 kW': colors.teal,
  'High power ≥150 and <350 kW': colors.blue,
  'Ultra-fast ≥350 kW': colors.navyAccent,
}
