import { createHash } from 'node:crypto'
import { readFile, writeFile, mkdir } from 'node:fs/promises'
import { dirname, join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const webRoot = resolve(scriptDir, '..')
const repoRoot = resolve(webRoot, '..')
const exportRoot = join(repoRoot, 'data', 'exports', 'tableau')
const preparationRoot = join(exportRoot, 'preparation')
const manifestPath = join(exportRoot, 'export_manifest.json')

const expectedStates = [
  'Baden-Württemberg',
  'Bayern',
  'Berlin',
  'Brandenburg',
  'Bremen',
  'Hamburg',
  'Hessen',
  'Mecklenburg-Vorpommern',
  'Niedersachsen',
  'Nordrhein-Westfalen',
  'Rheinland-Pfalz',
  'Saarland',
  'Sachsen',
  'Sachsen-Anhalt',
  'Schleswig-Holstein',
  'Thüringen',
]

function parseCsv(text) {
  const rows = []
  let row = []
  let field = ''
  let quoted = false

  for (let index = 0; index < text.length; index += 1) {
    const character = text[index]
    const next = text[index + 1]

    if (quoted) {
      if (character === '"' && next === '"') {
        field += '"'
        index += 1
      } else if (character === '"') {
        quoted = false
      } else {
        field += character
      }
      continue
    }

    if (character === '"' && field.length === 0) {
      quoted = true
    } else if (character === ',') {
      row.push(field)
      field = ''
    } else if (character === '\n') {
      row.push(field.endsWith('\r') ? field.slice(0, -1) : field)
      rows.push(row)
      row = []
      field = ''
    } else {
      field += character
    }
  }

  if (field.length > 0 || row.length > 0) {
    row.push(field.endsWith('\r') ? field.slice(0, -1) : field)
    rows.push(row)
  }

  const [headers, ...records] = rows
  if (!headers || headers.length === 0) {
    throw new Error('CSV has no header row')
  }

  return records
    .filter((values) => values.some((value) => value !== ''))
    .map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ''])))
}

function asNumber(value, fieldName) {
  if (value === '' || value === null || value === undefined) return null
  const number = Number(value)
  if (!Number.isFinite(number)) throw new Error(`Expected numeric value for ${fieldName}, got ${value}`)
  return number
}

function asInteger(value, fieldName) {
  const number = asNumber(value, fieldName)
  if (number === null || !Number.isInteger(number)) throw new Error(`Expected integer value for ${fieldName}`)
  return number
}

function asDate(value, fieldName) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) throw new Error(`Expected ISO date for ${fieldName}, got ${value}`)
  return value
}

function sum(rows, field) {
  return rows.reduce((total, row) => total + (row[field] ?? 0), 0)
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) throw new Error(`${label}: expected ${expected}, received ${actual}`)
}

function assertClose(actual, expected, label, tolerance = 0.000001) {
  if (Math.abs(actual - expected) > tolerance) throw new Error(`${label}: expected ${expected}, received ${actual}`)
}

async function readValidatedCsv(filename, expectedRows, manifestEntry = null) {
  const filePath = join(exportRoot, filename)
  const content = await readFile(filePath, 'utf8')
  const sha256 = createHash('sha256').update(content).digest('hex')
  if (manifestEntry) {
    assertEqual(sha256, manifestEntry.sha256, `${filename} SHA-256`)
    assertEqual(manifestEntry.row_count, expectedRows, `${filename} manifest row count`)
    assertEqual(manifestEntry.column_count, content.split('\n', 1)[0].split(',').length, `${filename} manifest column count`)
  }
  const rows = parseCsv(content)
  assertEqual(rows.length, expectedRows, `${filename} row count`)
  return { rows, sha256 }
}

const manifest = JSON.parse(await readFile(manifestPath, 'utf8'))
const manifestByFilename = new Map(manifest.exports.map((entry) => [entry.filename, entry]))

const nationalFile = await readValidatedCsv('national_charging_2026_09_30.csv', 1, manifestByFilename.get('national_charging_2026_09_30.csv'))
const stateChargingFile = await readValidatedCsv('state_charging_2026_09_30.csv', 16, manifestByFilename.get('state_charging_2026_09_30.csv'))
const stateComparisonFile = await readValidatedCsv('state_ev_charging_comparison_2026.csv', 16, manifestByFilename.get('state_ev_charging_comparison_2026.csv'))
const historyFile = await readValidatedCsv('kba_national_stock_history.csv', 33, manifestByFilename.get('kba_national_stock_history.csv'))
const powerBandFile = await readValidatedCsv('preparation/power_band_distribution_2026_09_30.csv', 4)
const statusFile = await readValidatedCsv('preparation/equipment_status_breakdown_2026_09_30.csv', 2)

const nationalSource = nationalFile.rows[0]
const national = {
  geographyName: nationalSource.geography_name,
  bnetzaReferenceDate: asDate(nationalSource.bnetza_reference_date, 'national.bnetza_reference_date'),
  equipmentCount: asInteger(nationalSource.equipment_count, 'national.equipment_count'),
  declaredChargingPointCount: asInteger(nationalSource.declared_charging_point_count, 'national.declared_charging_point_count'),
  chargingPointCount: asInteger(nationalSource.charging_point_count, 'national.charging_point_count'),
  normalChargingPointCount: asInteger(nationalSource.normal_charging_point_count, 'national.normal_charging_point_count'),
  fastChargingPointCount: asInteger(nationalSource.fast_charging_point_count, 'national.fast_charging_point_count'),
  pointsGe150Kw: asInteger(nationalSource.points_ge_150_kw, 'national.points_ge_150_kw'),
  pointsGe350Kw: asInteger(nationalSource.points_ge_350_kw, 'national.points_ge_350_kw'),
  equipmentNominalPowerMw: asNumber(nationalSource.equipment_nominal_power_mw, 'national.equipment_nominal_power_mw'),
  fastPointSharePct: asNumber(nationalSource.fast_point_share_pct, 'national.fast_point_share_pct'),
  pointsGe150SharePct: asNumber(nationalSource.points_ge_150_share_pct, 'national.points_ge_150_share_pct'),
  pointsGe350SharePct: asNumber(nationalSource.points_ge_350_share_pct, 'national.points_ge_350_share_pct'),
}

const stateCharging = stateChargingFile.rows.map((source) => ({
  stateName: source.state_name,
  bnetzaReferenceDate: asDate(source.bnetza_reference_date, 'stateCharging.bnetza_reference_date'),
  equipmentCount: asInteger(source.equipment_count, 'stateCharging.equipment_count'),
  chargingPointCount: asInteger(source.charging_point_count, 'stateCharging.charging_point_count'),
  normalChargingPointCount: asInteger(source.normal_charging_point_count, 'stateCharging.normal_charging_point_count'),
  fastChargingPointCount: asInteger(source.fast_charging_point_count, 'stateCharging.fast_charging_point_count'),
  pointsGe150Kw: asInteger(source.points_ge_150_kw, 'stateCharging.points_ge_150_kw'),
  pointsGe350Kw: asInteger(source.points_ge_350_kw, 'stateCharging.points_ge_350_kw'),
  equipmentNominalPowerMw: asNumber(source.equipment_nominal_power_mw, 'stateCharging.equipment_nominal_power_mw'),
  fastPointSharePct: asNumber(source.fast_point_share_pct, 'stateCharging.fast_point_share_pct'),
  pointsGe150SharePct: asNumber(source.points_ge_150_share_pct, 'stateCharging.points_ge_150_share_pct'),
  pointsGe350SharePct: asNumber(source.points_ge_350_share_pct, 'stateCharging.points_ge_350_share_pct'),
  chargingPointNationalSharePct: asNumber(source.charging_point_national_share_pct, 'stateCharging.charging_point_national_share_pct'),
}))

const stateComparison = stateComparisonFile.rows.map((source) => {
  const chargingPointCount = asInteger(source.charging_point_count, 'stateComparison.charging_point_count')
  const fastPointCount = asInteger(source.fast_point_count, 'stateComparison.fast_point_count')
  return {
    stateName: source.state_name,
    kbaReferenceDate: asDate(source.kba_reference_date, 'stateComparison.kba_reference_date'),
    bnetzaReferenceDate: asDate(source.bnetza_reference_date, 'stateComparison.bnetza_reference_date'),
    passengerCarStock: asInteger(source.passenger_car_stock, 'stateComparison.passenger_car_stock'),
    bevPassengerCarStock: asInteger(source.bev_passenger_car_stock, 'stateComparison.bev_passenger_car_stock'),
    phevPassengerCarStock: asInteger(source.phev_passenger_car_stock, 'stateComparison.phev_passenger_car_stock'),
    bevPenetrationPct: asNumber(source.bev_penetration_pct, 'stateComparison.bev_penetration_pct'),
    chargingPointCount,
    fastPointCount,
    fastPointSharePct: (fastPointCount / chargingPointCount) * 100,
    pointsGe150Kw: asInteger(source.points_ge_150_kw, 'stateComparison.points_ge_150_kw'),
    pointsGe350Kw: asInteger(source.points_ge_350_kw, 'stateComparison.points_ge_350_kw'),
    comparisonScope: source.comparison_scope,
    crossSourceTemporalLabel: source.cross_source_temporal_label,
    crossSourceDateNote: source.cross_source_date_note,
  }
})

const history = historyFile.rows.map((source) => ({
  stockDate: asDate(source.stock_date, 'history.stock_date'),
  sourceReportSnapshot: asDate(source.source_report_snapshot, 'history.source_report_snapshot'),
  bevStock: asInteger(source.bev_passenger_car_stock, 'history.bev_passenger_car_stock'),
  phevStock: asInteger(source.phev_passenger_car_stock, 'history.phev_passenger_car_stock'),
  passengerCarStock: asInteger(source.passenger_car_stock, 'history.passenger_car_stock'),
  combinedPluginStock: asInteger(source.combined_plugin_passenger_car_stock, 'history.combined_plugin_passenger_car_stock'),
  bevPenetrationPct: asNumber(source.bev_penetration_pct, 'history.bev_penetration_pct'),
  phevPenetrationPct: asNumber(source.phev_penetration_pct, 'history.phev_penetration_pct'),
}))

const powerBands = powerBandFile.rows.map((source) => ({
  order: asInteger(source.power_band_order, 'powerBands.order'),
  name: source.power_band,
  bnetzaReferenceDate: asDate(source.bnetza_reference_date, 'powerBands.bnetza_reference_date'),
  chargingPointCount: asInteger(source.charging_point_count, 'powerBands.charging_point_count'),
  chargingPointSharePct: asNumber(source.charging_point_share_pct, 'powerBands.charging_point_share_pct'),
}))

const equipmentStatus = statusFile.rows.map((source) => ({
  order: asInteger(source.status_order, 'equipmentStatus.order'),
  name: source.equipment_status,
  bnetzaReferenceDate: asDate(source.bnetza_reference_date, 'equipmentStatus.bnetza_reference_date'),
  equipmentCount: asInteger(source.equipment_count, 'equipmentStatus.equipment_count'),
  equipmentSharePct: asNumber(source.equipment_share_pct, 'equipmentStatus.equipment_share_pct'),
}))

assertEqual(national.geographyName, 'Germany', 'National geography')
assertEqual(national.bnetzaReferenceDate, '2026-09-30', 'BNetzA reference date')
assertEqual(national.equipmentCount, 117662, 'Equipment reconciliation')
assertEqual(national.chargingPointCount, 211253, 'Charging-point reconciliation')
assertEqual(national.normalChargingPointCount, 156155, 'Normal-point reconciliation')
assertEqual(national.fastChargingPointCount, 55098, 'Fast-point reconciliation')
assertEqual(national.pointsGe150Kw, 40950, '>=150 kW reconciliation')
assertEqual(national.pointsGe350Kw, 6950, '>=350 kW reconciliation')
assertClose(national.equipmentNominalPowerMw, 9215.4173, 'Nominal-power reconciliation')
assertEqual(sum(powerBands, 'chargingPointCount'), 211253, 'Mutually exclusive power-band total')
assertEqual(sum(equipmentStatus, 'equipmentCount'), 117662, 'Equipment-status total')
assertEqual(sum(stateCharging, 'equipmentCount'), 117662, 'State equipment total')
assertEqual(sum(stateCharging, 'chargingPointCount'), 211253, 'State charging-point total')
assertEqual(sum(stateCharging, 'fastChargingPointCount'), 55098, 'State fast-point total')
assertEqual(sum(stateCharging, 'pointsGe150Kw'), 40950, 'State >=150 kW total')
assertEqual(sum(stateCharging, 'pointsGe350Kw'), 6950, 'State >=350 kW total')
assertEqual(new Set(stateCharging.map((row) => row.stateName)).size, 16, 'Federal-state count')
assertEqual(new Set(stateCharging.map((row) => row.stateName)).size, expectedStates.length, 'Federal-state membership count')
assertEqual(JSON.stringify([...new Set(stateCharging.map((row) => row.stateName))].sort()), JSON.stringify([...expectedStates].sort()), 'Federal-state membership')
assertEqual(sum(stateComparison, 'bevPassengerCarStock'), 2362218, 'Sixteen-state BEV total')
assertEqual(sum(stateComparison, 'chargingPointCount'), 211253, 'Comparison charging-point total')
assertEqual(history.length, 33, 'Historical KBA observation count')
assertEqual(new Set(history.map((row) => row.stockDate)).size, 33, 'Historical KBA date uniqueness')
assertEqual(new Set(stateComparison.map((row) => row.stateName)).size, 16, 'Comparison federal-state count')
assertEqual(stateComparison[0].kbaReferenceDate, '2026-07-01', 'Comparison KBA date')

const sourceFiles = [
  { filename: 'national_charging_2026_09_30.csv', sha256: nationalFile.sha256, role: 'Batch 19 national charging fact' },
  { filename: 'state_charging_2026_09_30.csv', sha256: stateChargingFile.sha256, role: 'Batch 19 state charging fact' },
  { filename: 'state_ev_charging_comparison_2026.csv', sha256: stateComparisonFile.sha256, role: 'Batch 19 pre-combined state comparison fact' },
  { filename: 'kba_national_stock_history.csv', sha256: historyFile.sha256, role: 'Batch 19 national KBA history fact' },
  { filename: 'preparation/power_band_distribution_2026_09_30.csv', sha256: powerBandFile.sha256, role: 'Batch 21 mutually exclusive presentation fact' },
  { filename: 'preparation/equipment_status_breakdown_2026_09_30.csv', sha256: statusFile.sha256, role: 'Batch 21 equipment-status presentation fact' },
]

const dashboard = {
  meta: {
    exportVersion: manifest.export_version,
    preparationVersion: 'batch23-web-dashboard-2026-11-03-v1',
    sourceFiles,
    sourceDates: {
      bnetza: '2026-09-30',
      kba: '2026-07-01',
    },
    validation: {
      equipmentCount: 117662,
      chargingPointCount: 211253,
      normalChargingPointCount: 156155,
      fastChargingPointCount: 55098,
      pointsGe150Kw: 40950,
      pointsGe350Kw: 6950,
      equipmentNominalPowerMw: 9215.4173,
      nationalBevStock: 2365047,
      nationalPhevStock: 1226863,
      sixteenStateBevStock: 2362218,
      historicalKbaObservations: 33,
      federalStates: 16,
      powerBandsMutuallyExclusive: true,
    },
    map: {
      featureCount: 16,
      source: 'DeutschlandGeoJSON / GIS-DATA (DIVA-GIS)',
      license: 'Unlicense (source repository); attribution retained in web/public/data/geo-attribution.md',
      sourceUrl: 'https://github.com/isellsoap/deutschlandGeoJSON',
      assetUrl: 'https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/2_bundeslaender/4_niedrig.geo.json',
    },
  },
  national,
  powerBands,
  equipmentStatus,
  history,
  stateCharging,
  stateComparison,
}

const outputPath = join(webRoot, 'public', 'data', 'dashboard.json')
await mkdir(dirname(outputPath), { recursive: true })
await writeFile(outputPath, `${JSON.stringify(dashboard, null, 2)}\n`, 'utf8')

console.log(`Prepared ${outputPath}`)
console.log(`Validated ${stateCharging.length} federal states, ${history.length} KBA observations, and ${powerBands.length} mutually exclusive charging bands.`)
