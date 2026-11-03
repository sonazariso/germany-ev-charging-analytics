# Germany state-map geometry

The local `germany-states.geo.json` asset is the low-resolution federal-state
GeoJSON from [DeutschlandGeoJSON](https://github.com/isellsoap/deutschlandGeoJSON),
accessed on 2026-11-03 from
[`2_bundeslaender/4_niedrig.geo.json`](https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/2_bundeslaender/4_niedrig.geo.json).

- Coverage: 16 German federal states (`DE-BW` through `DE-TH`), validated against the state names in the approved Batch 19 state exports.
- Coordinate system: WGS84 longitude/latitude GeoJSON.
- Upstream credits: GIS-DATA / DIVA-GIS, as recorded by the source repository.
- Source-repository license: Unlicense. The source repository is archived; this local copy is kept so the deployed dashboard does not depend on a third-party map API.
- Local asset SHA-256: `9d5f5b14b48e262d2ce916cf7ab249f1342196e4dd0fde55a0af6132f995a54f`.

The geometry is used only for state-level visualization. Charging and vehicle
values come from the validated Batch 19 / Batch 21 exports and are not inferred
from the geometry.
