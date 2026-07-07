import { useEffect, useRef, useState } from 'react'
import maplibregl from 'maplibre-gl'
import { api } from './api.js'

const ROLES = [
  { key: 'organizer', label: '组织方', hint: '全局/裁判/调度' },
  { key: 'search', label: '搜索方', hint: '目标/变化检测' },
  { key: 'protection', label: '防护方', hint: '覆盖规划' },
]

// Tile URLs MUST be absolute: MapLibre fetches tiles in a Web Worker, where a
// relative URL resolves against the worker blob (not the page) and fails.
// Default: direct OSM (reliable, needs internet in the browser).
// Offline mode: set USE_OFFLINE_TILES=true to use the backend disk cache
// (pre-warm the demo area once online, then it works offline).
const USE_OFFLINE_TILES = false
const TILE_URL = USE_OFFLINE_TILES
  ? `${window.location.origin}/api/tiles/{z}/{x}/{y}.png`
  : 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

// Esri World Imagery: free satellite tiles, WGS-84 (aligns with GPS/OSM).
// Note tile template order is {z}/{y}/{x} for ArcGIS.
const SAT_URL = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'

const RASTER_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: 'raster', tiles: [TILE_URL], tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
    sat: {
      type: 'raster', tiles: [SAT_URL], tileSize: 256,
      attribution: 'Esri World Imagery',
    },
  },
  layers: [
    // Always-present background so the canvas is never blank, even with no
    // network / blocked tiles. Street/satellite raster draws on top.
    { id: 'bg', type: 'background', paint: { 'background-color': '#e8eef3' } },
    { id: 'osm', type: 'raster', source: 'osm' },
    { id: 'sat', type: 'raster', source: 'sat', layout: { visibility: 'none' } },
  ],
}

const ZONE_KINDS = [
  { kind: 'activity', label: '活动区', owner: 'organizer' },
  { kind: 'search', label: '搜索区', owner: 'search' },
  { kind: 'protection', label: '防护区', owner: 'protection' },
  { kind: 'no_go', label: '禁入区', owner: 'organizer' },
  { kind: 'safe', label: '安全区', owner: 'organizer' },
]
const kindLabel = (k) => (ZONE_KINDS.find((z) => z.kind === k) || {}).label || k

const EMPTY = { type: 'FeatureCollection', features: [] }

export default function App() {
  const mapEl = useRef(null)
  const map = useRef(null)
  const roleRef = useRef('organizer')
  const modeRef = useRef('none')
  const routeStart = useRef(null)
  const actId = useRef(null)
  const drawPts = useRef([])

  const [ready, setReady] = useState(false)
  const [role, setRole] = useState('organizer')
  const [mode, setMode] = useState('none')
  const [counts, setCounts] = useState(null)
  const [msg, setMsg] = useState('加载中…')
  const [det, setDet] = useState(null)
  const [basemap, setBasemap] = useState('street')
  const [drawKind, setDrawKind] = useState('activity')
  const [drawN, setDrawN] = useState(0)

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
      for (const id of ['zones', 'tracks', 'dets', 'cov-obs', 'cov-gaps', 'route', 'draw']) {
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
      // (no text 'symbol' layer: MapLibre text-field needs a 'glyphs' font
      // source; zones are identified by color legend + click popup instead.)
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
      // in-progress zone drawing (organizer)
      m.addLayer({
        id: 'draw-fill', type: 'fill', source: 'draw',
        paint: { 'fill-color': '#4f46e5', 'fill-opacity': 0.15 },
      })
      m.addLayer({
        id: 'draw-line', type: 'line', source: 'draw',
        paint: { 'line-color': '#4f46e5', 'line-width': 2, 'line-dasharray': [2, 1] },
      })
      m.addLayer({
        id: 'draw-pts', type: 'circle', source: 'draw',
        filter: ['==', ['geometry-type'], 'Point'],
        paint: { 'circle-radius': 4, 'circle-color': '#4f46e5', 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5 },
      })
      // change detections (COD) — magenta, drawn under object detections
      m.addLayer({
        id: 'det-change', type: 'circle', source: 'dets',
        filter: ['==', ['get', 'kind'], 'change'],
        paint: {
          'circle-radius': 6, 'circle-color': '#db2777',
          'circle-opacity': 0.55, 'circle-stroke-color': '#fff', 'circle-stroke-width': 1.5,
        },
      })
      m.addLayer({
        id: 'det-circle', type: 'circle', source: 'dets',
        filter: ['!=', ['get', 'kind'], 'change'],
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
        if (modeRef.current === 'draw') {
          drawPts.current.push([Number(e.lngLat.lng.toFixed(6)), Number(e.lngLat.lat.toFixed(6))])
          renderDraw()
          setDrawN(drawPts.current.length)
          return
        }
        const f = m.queryRenderedFeatures(e.point, { layers: ['det-circle', 'det-change'] })
        if (f.length) { setDet(f[0].properties); return }
        setDet(null)
        const zf = m.queryRenderedFeatures(e.point, { layers: ['zone-fill'] })
        if (zf.length) setMsg(`区域：${zf[0].properties.name}（${zf[0].properties.kind}）`)
      })
      for (const lyr of ['det-circle', 'det-change']) {
        m.on('mouseenter', lyr, () => { m.getCanvas().style.cursor = 'pointer' })
        m.on('mouseleave', lyr, () => { m.getCanvas().style.cursor = '' })
      }

      // load activity + initial state
      try {
        const acts = await api.activities()
        if (!acts.length) { setMsg('后端无活动，请点“重置演示”或检查播种'); return }
        const a = acts[0]
        actId.current = a.id
        m.jumpTo({ center: [a.center_lon, a.center_lat], zoom: a.zoom })
        setReady(true)
        await load('organizer')
        m.resize()
        setTimeout(() => m.resize(), 300)
      } catch (err) {
        console.error(err)
        setMsg('❌ 无法连接后端（:8000）。请先启动后端，再刷新本页。')
      }
    })

    return () => m.remove()
  }, [])

  async function load(r) {
    const id = actId.current
    if (id == null) return
    try {
      const s = await api.state(id, r)
      map.current.getSource('zones').setData(s.zones)
      map.current.getSource('tracks').setData(s.tracks)
      map.current.getSource('dets').setData(s.detections)
      setCounts(s.counts)
      setMsg(`活动 #${id} · ${s.activity.name}`)
    } catch (err) {
      console.error(err)
      setMsg('❌ 加载态势失败：' + err.message)
    }
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

  async function doChange() {
    const r = await api.change(actId.current, 'activity', 6)
    await load(roleRef.current)
    setMsg(`变化检测：新增 ${r.created} 个变化点（模拟）`)
  }

  async function doReset() {
    setMsg('重置演示中…')
    const r = await api.reset()
    actId.current = r.activity_id
    // clear planning overlays
    for (const s of ['cov-obs', 'cov-gaps', 'route']) map.current.getSource(s).setData({ type: 'FeatureCollection', features: [] })
    await load(roleRef.current)
    setMsg('演示已重置为初始 Hide-and-Seek 场景')
  }

  async function doUpload(e) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    try {
      const team = roleRef.current === 'protection' ? 'protection' : 'search'
      const r = await api.uploadTrack(actId.current, file, team, file.name)
      await load(roleRef.current)
      setMsg(`已上传航迹「${file.name}」：${r.points} 点（${team}）`)
    } catch (err) {
      setMsg('上传失败：' + err.message)
    }
  }

  async function doSimulate() {
    const s = await api.state(actId.current, 'organizer')
    const t = s.tracks.features[s.tracks.features.length - 1]
    if (!t) { setMsg('无航迹，请先上传或重置'); return }
    const r = await api.simulate(actId.current, t.properties.id, 6)
    await load(roleRef.current)
    setMsg(`沿航迹「${t.properties.name}」补充 ${r.created} 个模拟发现`)
  }

  async function reviewDet(status) {
    if (!det) return
    await api.review(det.id, status)
    setDet(null)
    load(roleRef.current)
    setMsg(`发现点 #${det.id} 标记为 ${status}`)
  }

  function switchBasemap(b) {
    setBasemap(b)
    const m = map.current
    if (!m) return
    m.setLayoutProperty('osm', 'visibility', b === 'street' ? 'visible' : 'none')
    m.setLayoutProperty('sat', 'visibility', b === 'sat' ? 'visible' : 'none')
  }

  function renderDraw() {
    const pts = drawPts.current
    const feats = []
    if (pts.length >= 3)
      feats.push({ type: 'Feature', geometry: { type: 'Polygon', coordinates: [[...pts, pts[0]]] } })
    if (pts.length >= 2)
      feats.push({ type: 'Feature', geometry: { type: 'LineString', coordinates: pts } })
    for (const p of pts) feats.push({ type: 'Feature', geometry: { type: 'Point', coordinates: p } })
    map.current.getSource('draw').setData({ type: 'FeatureCollection', features: feats })
  }

  function startDraw() {
    modeRef.current = 'draw'
    setMode('draw')
    routeStart.current = null
    drawPts.current = []
    setDrawN(0)
    renderDraw()
    setMsg(`绘制「${kindLabel(drawKind)}」：点击地图逐个加顶点，≥3 个后点“完成”`)
  }

  function cancelDraw() {
    modeRef.current = 'none'
    setMode('none')
    drawPts.current = []
    setDrawN(0)
    renderDraw()
    setMsg('已取消绘制')
  }

  async function finishDraw() {
    if (drawPts.current.length < 3) { setMsg('至少需要 3 个顶点'); return }
    const kd = ZONE_KINDS.find((z) => z.kind === drawKind)
    try {
      await api.addZone(actId.current, {
        name: kd.label, kind: kd.kind, role_owner: kd.owner, polygon: drawPts.current,
      })
      modeRef.current = 'none'
      setMode('none')
      drawPts.current = []
      setDrawN(0)
      renderDraw()
      await load(roleRef.current)
      setMsg(`已新增「${kd.label}」`)
    } catch (err) {
      setMsg('保存区域失败：' + err.message)
    }
  }

  return (
    <div className="app">
      <div ref={mapEl} className="map"
           style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh' }} />
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

        <div className="basemap">
          <span>底图</span>
          <button className={basemap === 'street' ? 'active' : ''} onClick={() => switchBasemap('street')}>街道</button>
          <button className={basemap === 'sat' ? 'active' : ''} onClick={() => switchBasemap('sat')}>卫星</button>
        </div>

        {counts && (
          <div className="counts">
            <div>区域 <b>{counts.zones}</b> · 轨迹 <b>{counts.tracks}</b> · 发现 <b>{counts.detections}</b></div>
            <div className="disc">真实 {counts.detections_real} · 模拟 {counts.detections_simulated}
              <span className="tag">MVP 披露</span></div>
          </div>
        )}

        <div className="actions">
          <button disabled={!ready} onClick={doChange}>变化检测 (COD)</button>
          <button disabled={!ready} onClick={doCoverage}>防护覆盖规划</button>
          <button disabled={!ready} className={mode === 'route' ? 'on' : ''} onClick={toggleRoute}>
            {mode === 'route' ? '取消路径' : '路径规划'}
          </button>
          <label className={ready ? 'filebtn' : 'filebtn dis'}>
            上传航迹 (GPX/CSV)
            <input type="file" accept=".gpx,.csv" disabled={!ready} onChange={doUpload} hidden />
          </label>
          <button disabled={!ready} onClick={doSimulate}>沿航迹补充发现</button>
          <button disabled={!ready} onClick={() => window.open(api.reportUrl(actId.current), '_blank')}>
            打开报告
          </button>
          <button disabled={!ready} className="reset" onClick={doReset}>重置演示</button>
        </div>

        {role === 'organizer' && (
          <div className="draw">
            <div className="draw-head">建区（组织方）</div>
            <div className="draw-kinds">
              {ZONE_KINDS.map((z) => (
                <button key={z.kind} disabled={mode === 'draw'}
                  className={drawKind === z.kind ? 'k active' : 'k'}
                  onClick={() => setDrawKind(z.kind)}>{z.label}</button>
              ))}
            </div>
            {mode !== 'draw' ? (
              <button disabled={!ready} onClick={startDraw}>绘制「{kindLabel(drawKind)}」</button>
            ) : (
              <div className="draw-live">
                <span>顶点 {drawN}</span>
                <button className="ok" disabled={drawN < 3} onClick={finishDraw}>完成</button>
                <button onClick={cancelDraw}>取消</button>
              </div>
            )}
          </div>
        )}

        <div className="legend">
          <span><i style={{ background: '#3b82f6' }} />活动区</span>
          <span><i style={{ background: '#f59e0b' }} />搜索区</span>
          <span><i style={{ background: '#10b981' }} />防护区</span>
          <span><i style={{ background: '#ef4444' }} />禁入区</span>
          <span><i style={{ background: '#14b8a6' }} />安全区</span>
          <span><i style={{ background: '#f59e0b', borderRadius: '50%' }} />发现</span>
          <span><i style={{ background: '#db2777', borderRadius: '50%' }} />变化</span>
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
