import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import { api } from './api.js'

const ROLES = [
  { key: 'organizer', label: '组织方', hint: '全局/裁判/调度' },
  { key: 'search', label: '搜索方', hint: '目标/变化检测' },
  { key: 'protection', label: '防护方', hint: '覆盖规划' },
]

const RASTER_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
}

const EMPTY = { type: 'FeatureCollection', features: [] }

export default function App() {
  const mapEl = useRef(null)
  const map = useRef(null)
  const roleRef = useRef('organizer')
  const modeRef = useRef('none')
  const routeStart = useRef(null)
  const actId = useRef(null)

  const [ready, setReady] = useState(false)
  const [role, setRole] = useState('organizer')
  const [mode, setMode] = useState('none')
  const [counts, setCounts] = useState(null)
  const [msg, setMsg] = useState('加载中…')
  const [det, setDet] = useState(null)

  // init map + data
  useEffect(() => {
    const m = new maplibregl.Map({
      container: mapEl.current,
      style: RASTER_STYLE,
      center: [120.13, 30.25],
      zoom: 14,
    })
    map.current = m
    m.addControl(new maplibregl.NavigationControl(), 'top-right')

    m.on('load', async () => {
      for (const id of ['zones', 'tracks', 'dets', 'cov-obs', 'cov-gaps', 'route']) {
        m.addSource(id, { type: 'geojson', data: EMPTY })
      }
      m.addLayer({
        id: 'zone-fill', type: 'fill', source: 'zones',
        paint: {
          'fill-color': ['match', ['get', 'kind'],
            'activity', '#3b82f6', 'search', '#f59e0b', 'protection', '#10b981',
            'no_go', '#ef4444', 'safe', '#14b8a6', 'staging', '#a78bfa', '#888'],
          'fill-opacity': ['match', ['get', 'kind'], 'no_go', 0.28, 0.12],
        },
      })
      m.addLayer({
        id: 'zone-line', type: 'line', source: 'zones',
        paint: {
          'line-color': ['match', ['get', 'kind'],
            'activity', '#2563eb', 'search', '#d97706', 'protection', '#059669',
            'no_go', '#dc2626', 'safe', '#0d9488', 'staging', '#7c3aed', '#666'],
          'line-width': 2,
        },
      })
      m.addLayer({
        id: 'zone-label', type: 'symbol', source: 'zones',
        layout: { 'text-field': ['get', 'name'], 'text-size': 12 },
        paint: { 'text-color': '#111', 'text-halo-color': '#fff', 'text-halo-width': 1.5 },
      })
      m.addLayer({
        id: 'track-line', type: 'line', source: 'tracks',
        paint: {
          'line-color': ['match', ['get', 'team'],
            'search', '#b45309', 'protection', '#047857', 'organizer', '#1d4ed8', '#555'],
          'line-width': 3, 'line-dasharray': [2, 1],
        },
      })
      m.addLayer({
        id: 'cov-gaps', type: 'circle', source: 'cov-gaps',
        paint: { 'circle-radius': 3, 'circle-color': '#ef4444', 'circle-opacity': 0.6 },
      })
      m.addLayer({
        id: 'cov-obs', type: 'circle', source: 'cov-obs',
        paint: {
          'circle-radius': 5, 'circle-color': '#10b981',
          'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5,
        },
      })
      m.addLayer({
        id: 'route-line', type: 'line', source: 'route',
        paint: { 'line-color': '#7c3aed', 'line-width': 4 },
      })
      m.addLayer({
        id: 'det-circle', type: 'circle', source: 'dets',
        paint: {
          'circle-radius': 7,
          'circle-color': ['match', ['get', 'status'],
            'confirmed', '#16a34a', 'rejected', '#9ca3af', '#f59e0b'],
          'circle-opacity': ['case', ['get', 'simulated'], 0.55, 0.95],
          'circle-stroke-color': '#111', 'circle-stroke-width': 1.5,
        },
      })

      m.on('click', (e) => {
        if (modeRef.current === 'route') return onRouteClick(e.lngLat)
        const f = m.queryRenderedFeatures(e.point, { layers: ['det-circle'] })
        if (f.length) setDet(f[0].properties)
        else setDet(null)
      })
      m.on('mouseenter', 'det-circle', () => { m.getCanvas().style.cursor = 'pointer' })
      m.on('mouseleave', 'det-circle', () => { m.getCanvas().style.cursor = '' })

      // load activity + initial state
      const acts = await api.activities()
      if (!acts.length) { setMsg('无活动，请先播种后端'); return }
      const a = acts[0]
      actId.current = a.id
      m.jumpTo({ center: [a.center_lon, a.center_lat], zoom: a.zoom })
      setReady(true)
      await load('organizer')
    })

    return () => m.remove()
  }, [])

  async function load(r) {
    const id = actId.current
    if (id == null) return
    const s = await api.state(id, r)
    map.current.getSource('zones').setData(s.zones)
    map.current.getSource('tracks').setData(s.tracks)
    map.current.getSource('dets').setData(s.detections)
    setCounts(s.counts)
    setMsg(`活动 #${id} · ${s.activity.name}`)
  }

  function switchRole(r) {
    roleRef.current = r
    setRole(r)
    setDet(null)
    load(r)
  }

  async function doCoverage() {
    const s = await api.state(actId.current, 'protection')
    const pz = s.zones.features.find((f) => f.properties.kind === 'protection')
    if (!pz) { setMsg('无防护区'); return }
    const cov = await api.coverage(actId.current, pz.properties.id, 120, 200)
    map.current.getSource('cov-obs').setData(cov.observation_points_geojson)
    map.current.getSource('cov-gaps').setData(cov.gaps_geojson)
    setMsg(`覆盖规划：观测点 ${cov.observation_points.length} · 覆盖率 ${(cov.coverage_ratio * 100).toFixed(0)}% · 盲区 ${cov.gap_count}`)
  }

  function toggleRoute() {
    const next = modeRef.current === 'route' ? 'none' : 'route'
    modeRef.current = next
    setMode(next)
    routeStart.current = null
    if (next === 'route') setMsg('路径规划：点击地图设置起点，再点终点（绕开禁入区）')
  }

  async function onRouteClick(lngLat) {
    const p = [Number(lngLat.lng.toFixed(6)), Number(lngLat.lat.toFixed(6))]
    if (!routeStart.current) {
      routeStart.current = p
      setMsg(`起点已设 ${p[1]},${p[0]}，请点终点`)
      return
    }
    const r = await api.route(actId.current, routeStart.current, p)
    map.current.getSource('route').setData(r.geojson)
    setMsg(`路径：${r.path.length} 点 · ${r.length_m} m · 绕开禁入区 ${r.avoided_no_go}`)
    routeStart.current = null
    modeRef.current = 'none'
    setMode('none')
  }

  async function reviewDet(status) {
    if (!det) return
    await api.review(det.id, status)
    setDet(null)
    load(roleRef.current)
    setMsg(`发现点 #${det.id} 标记为 ${status}`)
  }

  return (
    <div className="app">
      <div ref={mapEl} className="map" />
      <div className="panel">
        <h1>MSkit MVP</h1>
        <div className="sub">组织 / 搜索 / 防护 · 三方态势</div>

        <div className="roles">
          {ROLES.map((r) => (
            <button key={r.key} disabled={!ready}
              className={role === r.key ? 'role active' : 'role'}
              onClick={() => switchRole(r.key)} title={r.hint}>
              {r.label}
            </button>
          ))}
        </div>

        {counts && (
          <div className="counts">
            <div>区域 <b>{counts.zones}</b> · 轨迹 <b>{counts.tracks}</b> · 发现 <b>{counts.detections}</b></div>
            <div className="disc">真实 {counts.detections_real} · 模拟 {counts.detections_simulated}
              <span className="tag">MVP 披露</span></div>
          </div>
        )}

        <div className="actions">
          <button disabled={!ready} onClick={doCoverage}>防护覆盖规划</button>
          <button disabled={!ready} className={mode === 'route' ? 'on' : ''} onClick={toggleRoute}>
            {mode === 'route' ? '取消路径' : '路径规划'}
          </button>
          <button disabled={!ready} onClick={() => window.open(api.reportUrl(actId.current), '_blank')}>
            打开报告
          </button>
        </div>

        <div className="legend">
          <span><i style={{ background: '#3b82f6' }} />活动区</span>
          <span><i style={{ background: '#f59e0b' }} />搜索区</span>
          <span><i style={{ background: '#10b981' }} />防护区</span>
          <span><i style={{ background: '#ef4444' }} />禁入区</span>
          <span><i style={{ background: '#14b8a6' }} />安全区</span>
        </div>

        <div className="msg">{msg}</div>
      </div>

      {det && (
        <div className="det-card">
          <b>发现点 #{det.id}</b>
          <div>类别：{det.label} · 置信度 {Number(det.confidence).toFixed(2)}</div>
          <div>状态：{det.status} · {String(det.simulated) === 'true' ? '模拟/预置' : '真实推理'}</div>
          <div className="det-actions">
            <button className="ok" onClick={() => reviewDet('confirmed')}>确认</button>
            <button className="no" onClick={() => reviewDet('rejected')}>驳回</button>
            <button onClick={() => setDet(null)}>关闭</button>
          </div>
        </div>
      )}
    </div>
  )
}
