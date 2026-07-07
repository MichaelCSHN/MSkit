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
}
