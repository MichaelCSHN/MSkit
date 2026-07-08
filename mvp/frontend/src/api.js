// Thin API client. Uses the Vite dev proxy (/api -> :8000).
const BASE = '/api'

async function j(url, opts) {
  const r = await fetch(url, opts)
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`)
  return r.json()
}

export const api = {
  activities: () => j(`${BASE}/activities`),
  state: (id, role) => j(`${BASE}/activities/${id}/state?role=${role}`),
  simulate: (id, track_id, count = 6) =>
    j(`${BASE}/activities/${id}/detections/simulate`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ track_id, count }),
    }),
  review: (detId, status, note) =>
    j(`${BASE}/detections/${detId}/review`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status, note }),
    }),
  coverage: (id, zone_id, radius_m = 120, spacing_m = 150) =>
    j(`${BASE}/activities/${id}/coverage`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ zone_id, radius_m, spacing_m }),
    }),
  change: (id, zone_kind = 'activity', count = 5) =>
    j(`${BASE}/activities/${id}/detections/change`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ zone_kind, count }),
    }),
  reset: (center) => j(`${BASE}/demo/reset`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(center || {}),
  }),
  routeRoads: (id, waypoints, profile = 'foot') => j(`${BASE}/activities/${id}/route/roads`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ waypoints, profile }),
  }),
  addZone: (id, body) =>
    j(`${BASE}/activities/${id}/zones`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    }),
  route: (id, start, goal) =>
    j(`${BASE}/activities/${id}/route`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ start, goal }),
    }),
  uploadTrack: (id, file, team, name) => {
    const fd = new FormData()
    fd.append('file', file); fd.append('team', team); fd.append('name', name)
    return j(`${BASE}/activities/${id}/tracks`, { method: 'POST', body: fd })
  },
  reportUrl: (id) => `${BASE}/activities/${id}/report.html`,
  hiresRegions: () => j(`${BASE}/hires-regions`),
  geoscene: ([w, s, e, n]) => j(`${BASE}/geoscene/features?w=${w}&s=${s}&e=${e}&n=${n}`),

  // --- SAR (search & rescue) ---
  sarReset: (center) => j(`${BASE}/demo/sar`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(center || {}),
  }),
  placeTargets: (id, decoys = 4) =>
    j(`${BASE}/activities/${id}/sar/place-targets`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decoys }),
    }),
  droneSweep: (id, altitude_m = 90) =>
    j(`${BASE}/activities/${id}/sar/drone-sweep`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ altitude_m }),
    }),
  routePriority: (id, start, min_priority = 1) =>
    j(`${BASE}/activities/${id}/sar/route-priority`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ start, min_priority }),
    }),
  arrive: (id, point) =>
    j(`${BASE}/activities/${id}/sar/arrive`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ point }),
    }),
  sarStatus: (id) => j(`${BASE}/activities/${id}/sar/status`),
  setPriority: (detId, priority) =>
    j(`${BASE}/detections/${detId}/priority`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ priority }),
    }),
  focusArea: (id, min_priority = 60) =>
    j(`${BASE}/activities/${id}/sar/focus-area`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ min_priority }),
    }),
}
