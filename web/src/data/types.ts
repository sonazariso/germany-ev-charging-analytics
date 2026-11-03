export interface NationalCharging {
  geographyName: string
  bnetzaReferenceDate: string
  equipmentCount: number
  declaredChargingPointCount: number
  chargingPointCount: number
  normalChargingPointCount: number
  fastChargingPointCount: number
  pointsGe150Kw: number
  pointsGe350Kw: number
  equipmentNominalPowerMw: number
  fastPointSharePct: number
  pointsGe150SharePct: number
  pointsGe350SharePct: number
}

export interface PowerBand {
  order: number
  name: string
  bnetzaReferenceDate: string
  chargingPointCount: number
  chargingPointSharePct: number
}

export interface EquipmentStatus {
  order: number
  name: string
  bnetzaReferenceDate: string
  equipmentCount: number
  equipmentSharePct: number
}

export interface NationalHistoryRow {
  stockDate: string
  sourceReportSnapshot: string
  bevStock: number
  phevStock: number
  passengerCarStock: number
  combinedPluginStock: number
  bevPenetrationPct: number
  phevPenetrationPct: number
}

export interface StateCharging {
  stateName: string
  bnetzaReferenceDate: string
  equipmentCount: number
  chargingPointCount: number
  normalChargingPointCount: number
  fastChargingPointCount: number
  pointsGe150Kw: number
  pointsGe350Kw: number
  equipmentNominalPowerMw: number
  fastPointSharePct: number
  pointsGe150SharePct: number
  pointsGe350SharePct: number
  chargingPointNationalSharePct: number
}

export interface StateComparison {
  stateName: string
  kbaReferenceDate: string
  bnetzaReferenceDate: string
  passengerCarStock: number
  bevPassengerCarStock: number
  phevPassengerCarStock: number
  bevPenetrationPct: number
  chargingPointCount: number
  fastPointCount: number
  fastPointSharePct: number
  pointsGe150Kw: number
  pointsGe350Kw: number
  comparisonScope: string
  crossSourceTemporalLabel: string
  crossSourceDateNote: string
}

export interface DashboardMeta {
  exportVersion: string
  preparationVersion: string
  sourceFiles: Array<{ filename: string; sha256: string; role: string }>
  sourceDates: { bnetza: string; kba: string }
  validation: {
    equipmentCount: number
    chargingPointCount: number
    normalChargingPointCount: number
    fastChargingPointCount: number
    pointsGe150Kw: number
    pointsGe350Kw: number
    equipmentNominalPowerMw: number
    nationalBevStock: number
    nationalPhevStock: number
    sixteenStateBevStock: number
    historicalKbaObservations: number
    federalStates: number
    powerBandsMutuallyExclusive: boolean
  }
  map: {
    featureCount: number
    source: string
    license: string
    sourceUrl: string
    assetUrl: string
  }
}

export interface DashboardData {
  meta: DashboardMeta
  national: NationalCharging
  powerBands: PowerBand[]
  equipmentStatus: EquipmentStatus[]
  history: NationalHistoryRow[]
  stateCharging: StateCharging[]
  stateComparison: StateComparison[]
}

export interface GeoFeature {
  type: 'Feature'
  id?: string | number
  properties: { id?: string; name: string; type?: string }
  geometry: unknown
}

export interface GeoJsonFeatureCollection {
  type: 'FeatureCollection'
  features: GeoFeature[]
}
