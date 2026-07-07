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
// priority band per docs §7.4 (0-100, P0 highest)
const bandOf = (p) => (p >= 80 ? 'P0' : p >= 60 ? 'P1' : p >= 40 ? 'P2' : 'P3')
const PRIO_SCORE = { P0: 90, P1: 70, P2: 50, P3: 20 }

// small circle polygon ring [[lon,lat],...] around a point (meters radius)
function circlePoly(lon, lat, rM = 8, n = 18) {
  const dLat = rM / 111320
  const dLon = rM / (111320 * Math.cos((lat * Math.PI) / 180))
  const ring = []
  for (let i = 0; i <= n; i++) {
    const a = (2 * Math.PI * i) / n
    ring.push([lon + dLon * Math.cos(a), lat + dLat * Math.sin(a)])
  }
  return ring
}

// per (scenario, role) step guide — the "what do I do, in what order" panel
const GUIDE = {
  hs: {
    organizer: { title: '组织方 · 统揽 / 裁判 / 归档', steps: [
      '建区：下方选类型 → 地图点多个顶点 → 完成',
      '点橙色“发现点” → 确认 / 驳回（裁决）',
      '（可选）路径规划：点途经点 → 双击结束',
      '打开报告导出'] },
    search: { title: '搜索方 · 找目标 / 报证据', steps: [
      '变化检测 (COD)：找新增/移动/消失',
      '上传航迹(GPX/CSV) 或 沿航迹补充发现',
      '点发现点复核'] },
    protection: { title: '防护方 · 覆盖 / 巡查', steps: [
      '防护覆盖规划：看观测点与盲区',
      '路径规划：巡查路线'] },
  },
  sar: {
    organizer: { title: '搜救·组织方 · 建场 / 布点（真值你可见）', steps: [
      '拖地图到目标区域 → 📍设为起点',
      '建区：画“重点搜索区”（先验范围）',
      '预置隐藏目标（对搜索方不可见）',
      '切到“搜索方”移交任务'] },
    search: { title: '搜救·搜索方 · 检出 → 核查 → 到达', steps: [
      '无人机拉网：检出橙色“候选点”(P0–P3)',
      '点候选点 → 改优先级 / 到达核查',
      '更新搜索区(聚焦热点) → 优先级路由 或手动路径(点途经点→双击结束)',
      '手动路线会提示是否穿禁入区/偏离；到真目标即完成'] },
  },
}

const EMPTY = { type: 'FeatureCollection', features: [] }

export default function App() {
  const mapEl = useRef(null)
  const map = useRef(null)
  const roleRef = useRef('organizer')
  const modeRef = useRef('none')
  const routeStart = useRef(null)
  const routeWps = useRef([])
  const actId = useRef(null)
  const drawPts = useRef([])
  const coordRef = useRef(null)
  const routeProfileRef = useRef('foot')
  const scenarioRef = useRef('hide_and_seek')
  const dvMap = useRef(null)
  const dvMapEl = useRef(null)
  const dvMarker = useRef(null)

  const [ready, setReady] = useState(false)
  const [role, setRole] = useState('organizer')
  const [mode, setMode] = useState('none')
  const [counts, setCounts] = useState(null)
  const [msg, setMsg] = useState('加载中…')
  const [det, setDet] = useState(null)
  const [droneView, setDroneView] = useState(null)
  const [basemap, setBasemap] = useState('street')
  const [is3D, setIs3D] = useState(false)
  const [drawKind, setDrawKind] = useState('activity')
  const [drawN, setDrawN] = useState(0)
  const [routeProfile, setRouteProfile] = useState('foot')
  const [scenario, setScenario] = useState('hide_and_seek')
  const [showGuide, setShowGuide] = useState(true)
  const [decoys, setDecoys] = useState(4)
  const [altitude, setAltitude] = useState(90)
  const [sarStat, setSarStat] = useState(null)

  // init map + data
  useEffect(() => {
    const m = new maplibregl.Map({
      container: mapEl.current,
      style: RASTER_STYLE,
      center: [120.13, 30.25],
      zoom: 14,
      maxPitch: 85,   // MapLibre max (GE-like near-horizon tilt); default is 60
    })
    map.current = m
    m.addControl(new maplibregl.NavigationControl(), 'top-right')

    m.on('load', async () => {
      for (const id of ['zones', 'tracks', 'dets', 'cov-obs', 'cov-gaps', 'route', 'draw', 'sweep', 'markers', 'beacon']) {
        m.addSource(id, { type: 'geojson', data: EMPTY })
      }
      // DEM for 3D terrain (free AWS Terrarium tiles); terrain toggled on demand
      m.addSource('terrain-dem', {
        type: 'raster-dem',
        tiles: ['https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'],
        encoding: 'terrarium', tileSize: 256, maxzoom: 15,
      })
      m.addLayer({
        id: 'zone-fill', type: 'fill', source: 'zones',
        paint: {
          'fill-color': ['match', ['get', 'kind'],
            'activity', '#ffffff', 'search', '#f59e0b', 'protection', '#3b82f6',
            'no_go', '#ef4444', 'safe', '#14b8a6', 'hotspot', '#f97316', 'staging', '#a78bfa', '#888'],
          'fill-opacity': ['match', ['get', 'kind'], 'no_go', 0.28, 'activity', 0.10, 'hotspot', 0.15, 'protection', 0.12, 0.12],
        },
      })
      m.addLayer({
        id: 'zone-line', type: 'line', source: 'zones',
        paint: {
          'line-color': ['match', ['get', 'kind'],
            'activity', '#ffffff', 'search', '#d97706', 'protection', '#1d4ed8',
            'no_go', '#dc2626', 'safe', '#0d9488', 'hotspot', '#ea580c', 'staging', '#7c3aed', '#666'],
          'line-width': ['match', ['get', 'kind'], 'activity', 2.5, 'hotspot', 2.5, 2],
        },
      })
      // (no text 'symbol' layer: MapLibre text-field needs a 'glyphs' font
      // source; zones are identified by color legend + click popup instead.)
      // dashed outline for auto-generated hotspot sub-zones (search-area update)
      m.addLayer({
        id: 'zone-hotspot', type: 'line', source: 'zones',
        filter: ['==', ['get', 'kind'], 'hotspot'],
        paint: { 'line-color': '#ea580c', 'line-width': 3, 'line-dasharray': [2, 1.5] },
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
        id: 'sweep-line', type: 'line', source: 'sweep',
        paint: { 'line-color': '#06b6d4', 'line-width': 1.5, 'line-opacity': 0.7, 'line-dasharray': [1, 1] },
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
        id: 'route-pts', type: 'circle', source: 'route',
        filter: ['==', ['geometry-type'], 'Point'],
        paint: { 'circle-radius': 5, 'circle-color': '#7c3aed', 'circle-stroke-color': '#fff', 'circle-stroke-width': 2 },
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
          // in SAR, candidates carry priority 0..100 → bigger = more urgent
          'circle-radius': ['case', ['>', ['get', 'priority'], 0],
            ['+', 5, ['/', ['get', 'priority'], 11]], 7],
          'circle-color': ['match', ['get', 'status'],
            'confirmed', '#16a34a', 'rejected', '#9ca3af', '#f59e0b'],
          'circle-opacity': ['case', ['get', 'simulated'], 0.6, 0.95],
          'circle-stroke-color': '#111', 'circle-stroke-width': 1.5,
        },
      })

      // SAR ground-truth markers (target = red & large, decoy = grey)
      m.addLayer({
        id: 'marker-pt', type: 'circle', source: 'markers',
        paint: {
          'circle-radius': ['match', ['get', 'kind'], 'target', 9, 5],
          'circle-color': ['match', ['get', 'kind'], 'target', '#dc2626', '#6b7280'],
          'circle-stroke-color': '#fff', 'circle-stroke-width': 2,
        },
      })
      // 3D beacon (red pillar) at the target — stands up when tilted
      m.addLayer({
        id: 'beacon-3d', type: 'fill-extrusion', source: 'beacon',
        paint: {
          'fill-extrusion-color': '#ef4444', 'fill-extrusion-height': 60,
          'fill-extrusion-base': 0, 'fill-extrusion-opacity': 0.85,
        },
      })

      // finish a multi-waypoint route by double-click or right-click
      m.on('dblclick', (e) => {
        if (modeRef.current === 'route') { e.preventDefault(); finishRoute() }
      })
      m.on('contextmenu', () => { if (modeRef.current === 'route') finishRoute() })

      // live coordinate readout (updates a DOM node directly, no re-render)
      m.on('mousemove', (e) => {
        if (coordRef.current)
          coordRef.current.textContent = `${e.lngLat.lat.toFixed(5)}, ${e.lngLat.lng.toFixed(5)}  z${m.getZoom().toFixed(1)}`
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
        if (f.length) {
          const ft = f[0]
          const lon = ft.geometry.coordinates[0], lat = ft.geometry.coordinates[1]
          setDet({ ...ft.properties, _lon: lon, _lat: lat })
          if (scenarioRef.current === 'sar')
            setDroneView({ lon, lat, label: `候选 #${ft.properties.id} · ${bandOf(ft.properties.priority)}` })
          return
        }
        setDet(null)
        const zf = m.queryRenderedFeatures(e.point, { layers: ['zone-fill'] })
        if (zf.length) setMsg(`区域：${zf[0].properties.name}（${zf[0].properties.kind}）`)
      })
      for (const lyr of ['det-circle', 'det-change']) {
        m.on('mouseenter', lyr, () => { m.getCanvas().style.cursor = 'pointer' })
        m.on('mouseleave', lyr, () => { m.getCanvas().style.cursor = '' })
      }

      // load activity + initial state; auto-retry until the backend is reachable
      const bootstrap = async () => {
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
          setMsg('❌ 无法连接后端(:8000)，5 秒后自动重试…（请确认后端已启动）')
          setTimeout(bootstrap, 5000)
        }
      }
      bootstrap()
    })

    return () => m.remove()
  }, [])

  // drone aerial view = interactive mini-map on the SR tile service (pan/zoom)
  useEffect(() => {
    if (!droneView) {
      if (dvMap.current) { dvMap.current.remove(); dvMap.current = null; dvMarker.current = null }
      return
    }
    const center = [droneView.lon, droneView.lat]
    if (dvMap.current) {
      dvMap.current.jumpTo({ center, zoom: 18 })
      if (dvMarker.current) dvMarker.current.setLngLat(center)
      return
    }
    if (!dvMapEl.current) return
    const mm = new maplibregl.Map({
      container: dvMapEl.current,
      style: {
        version: 8,
        sources: {
          sr: {
            type: 'raster',
            tiles: [`${window.location.origin}/api/sr-tiles/{z}/{x}/{y}.jpg?v=4`],
            tileSize: 256, minzoom: 14, maxzoom: 19,
          },
        },
        layers: [{ id: 'sr', type: 'raster', source: 'sr' }],
      },
      center, zoom: 18, minZoom: 15, maxZoom: 19, attributionControl: false,
    })
    dvMap.current = mm
    mm.on('load', () => mm.resize())
    dvMarker.current = new maplibregl.Marker({ color: '#dc2626' }).setLngLat(center).addTo(mm)
  }, [droneView])

  async function load(r) {
    const id = actId.current
    if (id == null) return
    try {
      const s = await api.state(id, r)
      map.current.getSource('zones').setData(s.zones)
      map.current.getSource('tracks').setData(s.tracks)
      map.current.getSource('dets').setData(s.detections)
      map.current.getSource('markers').setData(s.markers || EMPTY)
      const targets = (s.markers?.features || []).filter((f) => f.properties.kind === 'target')
      map.current.getSource('beacon').setData({
        type: 'FeatureCollection',
        features: targets.map((f) => ({
          type: 'Feature',
          geometry: { type: 'Polygon', coordinates: [circlePoly(f.geometry.coordinates[0], f.geometry.coordinates[1])] },
        })),
      })
      setCounts(s.counts)
      setScenario(s.activity.scenario)
      scenarioRef.current = s.activity.scenario
      setMsg(`活动 #${id} · ${s.activity.name}`)
      if (s.activity.scenario === 'sar') {
        try { setSarStat(await api.sarStatus(id)) } catch { /* ignore */ }
      } else setSarStat(null)
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
    routeWps.current = []
    map.current.getSource('route').setData(EMPTY)
    if (next === 'route') {
      map.current.doubleClickZoom.disable()
      setMsg('路径规划：依次点选多个途经点；双击或右键结束（自动吸附道路）')
    } else {
      map.current.doubleClickZoom.enable()
      setMsg('已退出路径规划')
    }
  }

  function pickProfile(p) {
    setRouteProfile(p)
    routeProfileRef.current = p
  }

  function renderRouteWps() {
    const wps = routeWps.current
    const feats = wps.map((p) => ({ type: 'Feature', geometry: { type: 'Point', coordinates: p } }))
    if (wps.length >= 2)
      feats.unshift({ type: 'Feature', geometry: { type: 'LineString', coordinates: wps } })
    map.current.getSource('route').setData({ type: 'FeatureCollection', features: feats })
  }

  function onRouteClick(lngLat) {
    routeWps.current.push([Number(lngLat.lng.toFixed(6)), Number(lngLat.lat.toFixed(6))])
    renderRouteWps()
    setMsg(`途经点 ${routeWps.current.length}（双击 / 右键结束）`)
  }

  async function finishRoute() {
    const wps = routeWps.current.slice()
    modeRef.current = 'none'
    setMode('none')
    map.current.doubleClickZoom.enable()
    if (wps.length < 2) {
      setMsg('至少需要 2 个途经点')
      map.current.getSource('route').setData(EMPTY)
      routeWps.current = []
      return
    }
    setMsg('规划中…')
    try {
      const r = await api.routeRoads(actId.current, wps, routeProfileRef.current)
      map.current.getSource('route').setData(r.geojson)
      const how = { foot: '徒步(BRouter)', car: '机动车(OSRM)', offroad: '越野直连(A*)' }[r.profile] || r.profile
      const note = (routeProfileRef.current !== 'offroad' && r.profile === 'offroad') ? '（在线路由不可达，已回退）' : ''
      const warn = r.warnings && r.warnings.length ? ` ⚠ ${r.warnings.join('、')}` : ''
      setMsg(`路径 ${r.length_m} m · ${how}${note}${warn}`)
    } catch (err) {
      setMsg('路由失败：' + err.message)
    }
    routeWps.current = []
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

  function toggle3D() {
    const m = map.current
    if (!m) return
    const next = !is3D
    setIs3D(next)
    if (next) {
      m.setTerrain({ source: 'terrain-dem', exaggeration: 1.4 })
      m.easeTo({ pitch: 70, duration: 800 })
      setMsg('3D 地形已开：右键拖动倾斜/旋转（可到 85°）；DEM 连不上则为平面')
    } else {
      m.setTerrain(null)
      m.easeTo({ pitch: 0, bearing: 0, duration: 600 })
      setMsg('已回到 2D')
    }
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

  // ---- scenario + SAR ----
  async function reloadActivity() {
    const acts = await api.activities()
    if (!acts.length) return
    const a = acts[0]
    actId.current = a.id
    map.current.jumpTo({ center: [a.center_lon, a.center_lat], zoom: a.zoom })
    for (const src of ['cov-obs', 'cov-gaps', 'route', 'sweep', 'draw']) map.current.getSource(src).setData(EMPTY)
    roleRef.current = 'organizer'
    setRole('organizer')
    await load('organizer')
  }

  async function switchScenario(kind) {
    setMsg('切换场景中…')
    if (kind === 'sar') await api.sarReset()
    else await api.reset()
    await reloadActivity()
    setMsg(kind === 'sar' ? '已切到搜救(SAR)' : '已切到捉迷藏')
  }

  async function locateHere() {
    // use the current MAP VIEW center (where the user panned to), not GPS
    const c = map.current.getCenter()
    const center = { lat: +c.lat.toFixed(6), lon: +c.lng.toFixed(6) }
    setMsg('以当前地图中心重建起始区域…')
    if (scenario === 'sar') await api.sarReset(center)
    else await api.reset(center)
    await reloadActivity()
    setMsg(`起始区域已设到当前视图中心 ${center.lat}, ${center.lon}`)
  }

  async function doPlaceTargets() {
    const r = await api.placeTargets(actId.current, decoys)
    map.current.getSource('sweep').setData(EMPTY)
    await load(roleRef.current)
    setMsg(`已预置隐藏目标：1 目标 + ${r.decoys} 疑似（搜索方不可见）`)
  }

  async function doDroneSweep() {
    const r = await api.droneSweep(actId.current, altitude)
    map.current.getSource('sweep').setData(r.sweep)
    await load(roleRef.current)
    // open a simulated drone aerial view of the most salient candidate
    const s = await api.state(actId.current, 'organizer')
    const feats = [...s.detections.features].sort(
      (a, b) => (b.properties.priority || 0) - (a.properties.priority || 0))
    if (feats.length) {
      const f = feats[0]
      setDroneView({ lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1],
        label: `候选 #${f.properties.id} · ${bandOf(f.properties.priority)}` })
    } else {
      const sz = s.zones.features.find((z) => z.properties.kind === 'search')
      if (sz) {
        const ring = sz.geometry.coordinates[0]
        setDroneView({ lon: ring.reduce((a, p) => a + p[0], 0) / ring.length,
          lat: ring.reduce((a, p) => a + p[1], 0) / ring.length, label: '搜索区' })
      }
    }
    setMsg(`无人机拉网：足迹 ${r.footprint_m}m · 覆盖 ${(r.coverage_ratio * 100).toFixed(0)}% · 检出候选 ${r.detected}`)
  }

  async function doRoutePriority() {
    const s = await api.state(actId.current, 'organizer')
    const safe = s.zones.features.find((f) => f.properties.kind === 'safe' && f.properties.name.includes('出发'))
      || s.zones.features.find((f) => f.properties.kind === 'safe')
    if (!safe) { setMsg('无出发安全区'); return }
    const ring = safe.geometry.coordinates[0]
    const start = [
      ring.reduce((a, p) => a + p[0], 0) / ring.length,
      ring.reduce((a, p) => a + p[1], 0) / ring.length,
    ]
    try {
      const r = await api.routePriority(actId.current, start, 60)
      map.current.getSource('route').setData(r.geojson)
      setMsg(`优先级路由：串联 ${r.stops} 个 P1+ 候选 · ${r.length_m} m（从出发点贪心）`)
    } catch (err) {
      setMsg('路由失败（可能没有 ≥3 优先级候选）：' + err.message)
    }
  }

  async function setPrio(score) {
    if (!det) return
    await api.setPriority(det.id, score)
    setDet({ ...det, priority: score })
    load(roleRef.current)
    setMsg(`发现点 #${det.id} 优先级设为 ${bandOf(score)} (${score})`)
  }

  async function doFocusArea() {
    try {
      const r = await api.focusArea(actId.current, 60)
      await load(roleRef.current)
      setMsg(`搜索区已更新：由 ${r.from_candidates} 个 P1+ 候选生成热点子区`)
    } catch (err) {
      setMsg('更新搜索区失败（可能无 P1+ 候选）：' + err.message)
    }
  }

  async function arriveAt() {
    if (!det) return
    const r = await api.arrive(actId.current, [det._lon, det._lat])
    try { setSarStat(await api.sarStatus(actId.current)) } catch { /* ignore */ }
    if (r.complete) setMsg(`🎯 到达目标！任务完成（距离 ${r.distance_m}m）`)
    else setMsg(`核查此候选：距真目标 ${r.distance_m}m —— 不是目标，继续下一个`)
  }

  const guide = (GUIDE[scenario === 'sar' ? 'sar' : 'hs'] || {})[role]

  return (
    <div className="app">
      <div ref={mapEl} className="map"
           style={{ position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh' }} />
      <div className="coord" ref={coordRef}>移动鼠标查看经纬度</div>
      <div className="panel">
        <h1>MSkit MVP</h1>
        <div className="sub">组织 / 搜索 / 防护 · 三方态势</div>

        <div className="scenario">
          <span>场景</span>
          <button disabled={!ready} className={scenario !== 'sar' ? 'active' : ''} onClick={() => switchScenario('hs')} title="捉迷藏/对抗：组织+搜索+防护三方">捉迷藏</button>
          <button disabled={!ready} className={scenario === 'sar' ? 'active' : ''} onClick={() => switchScenario('sar')} title="野外搜救：仅组织+搜索；隐藏目标+无人机检出+到达">搜救</button>
        </div>

        <div className="roles">
          {(scenario === 'sar' ? ROLES.filter((r) => r.key !== 'protection') : ROLES).map((r) => (
            <button key={r.key} disabled={!ready}
              className={role === r.key ? 'role active' : 'role'}
              onClick={() => switchRole(r.key)} title={r.hint}>
              {r.label}
            </button>
          ))}
        </div>

        <div className="basemap">
          <span>底图</span>
          <button className={basemap === 'street' ? 'active' : ''} onClick={() => switchBasemap('street')} title="OpenStreetMap 街道底图">街道</button>
          <button className={basemap === 'sat' ? 'active' : ''} onClick={() => switchBasemap('sat')} title="Esri 卫星影像底图">卫星</button>
          <button className={is3D ? 'active' : ''} onClick={toggle3D} title="3D 地形起伏 + 倾斜（右键拖动旋转）">3D</button>
          <button disabled={!ready} onClick={locateHere} title="以当前地图视图中心为起始区域">📍设为起点</button>
        </div>

        {guide && showGuide && (
          <div className="guide">
            <div className="guide-head">
              <span>👉 {guide.title}</span>
              <button className="guide-x" onClick={() => setShowGuide(false)} title="收起引导">×</button>
            </div>
            <ol>{guide.steps.map((s, i) => <li key={i}>{s}</li>)}</ol>
          </div>
        )}
        {guide && !showGuide && (
          <button className="guide-show" onClick={() => setShowGuide(true)}>❔ 显示步骤引导</button>
        )}

        {counts && (
          <div className="counts">
            <div>区域 <b>{counts.zones}</b> · 轨迹 <b>{counts.tracks}</b> · 发现 <b>{counts.detections}</b></div>
            <div className="disc">真实 {counts.detections_real} · 模拟 {counts.detections_simulated}
              <span className="tag">MVP 披露</span></div>
          </div>
        )}

        {scenario === 'sar' && (
          <div className="sar">
            <div className="sar-head">搜救 (SAR) · {role === 'organizer' ? '组织方' : '搜索方'}</div>
            {sarStat && (
              <div className="sar-stat">
                目标{sarStat.target_revealed ? '已检出' : '未检出'} · 疑似 {sarStat.decoys_revealed}/{sarStat.decoys}
                {sarStat.complete && <b style={{ color: '#16a34a' }}> · 任务完成 ✅</b>}
              </div>
            )}
            {role === 'organizer' && (
              <div className="sar-row">
                <label title="疑似干扰点数量">疑似 <input type="number" min="0" max="12" value={decoys} onChange={(e) => setDecoys(+e.target.value)} /></label>
                <button disabled={!ready} onClick={doPlaceTargets} title="在搜索区随机布 1 个真目标 + N 个疑似，仅组织方可见">预置隐藏目标</button>
              </div>
            )}
            {role === 'search' && (
              <>
                <div className="sar-row">
                  <label title="飞行高度越高，相机足迹越大，覆盖越广">高度 <input type="number" min="30" max="200" value={altitude} onChange={(e) => setAltitude(+e.target.value)} />m</label>
                  <button disabled={!ready} onClick={doDroneSweep} title="按高度决定相机足迹，拉网扫描搜索区并检出候选点">无人机拉网</button>
                </div>
                <button disabled={!ready} onClick={doRoutePriority} title="从出发安全区贪心串联高优先级候选点">优先级路由（串高优先候选）</button>
                <button disabled={!ready} onClick={doFocusArea} title="按 P1+ 候选聚类生成热点搜索子区（§7.5 搜索区更新）">更新搜索区（聚焦热点）</button>
                <div className="sar-hint">点候选点 → 改优先级 / 到达核查（是否真目标）</div>
              </>
            )}
          </div>
        )}

        <div className="actions">
          <button disabled={!ready} onClick={doChange} title="变化检测(COD)：对比基线找新增/移动/消失的变化点（模拟）">变化检测 (COD)</button>
          <button disabled={!ready} onClick={doCoverage} title="在防护区内生成观测点、覆盖率与盲区">防护覆盖规划</button>
          <div className="routemode">
            <span>路线</span>
            {[['foot', '步行'], ['car', '道路'], ['offroad', '越野']].map(([k, l]) => (
              <button key={k} className={routeProfile === k ? 'active' : ''}
                onClick={() => pickProfile(k)} title={k === 'foot' ? '徒步/小路(BRouter)，搜救默认' : k === 'car' ? '机动车道(OSRM)，会绕大路' : '直连绕禁入区(A*)，最直'}>
                {l}
              </button>
            ))}
          </div>
          <button disabled={!ready} className={mode === 'route' ? 'on' : ''} onClick={toggleRoute}
            title="点选多个途经点，双击/右键结束；按上方“路线”方式吸附">
            {mode === 'route' ? '取消路径' : '路径规划'}
          </button>
          <label className={ready ? 'filebtn' : 'filebtn dis'} title="导入无人机 GPX/CSV 航迹">
            上传航迹 (GPX/CSV)
            <input type="file" accept=".gpx,.csv" disabled={!ready} onChange={doUpload} hidden />
          </label>
          <button disabled={!ready} onClick={doSimulate} title="沿最新航迹补充若干模拟发现点">沿航迹补充发现</button>
          <button disabled={!ready} onClick={() => window.open(api.reportUrl(actId.current), '_blank')}
            title="打开含“真实 vs 模拟”披露的 HTML 报告">
            打开报告
          </button>
          <button disabled={!ready} className="reset" onClick={doReset} title="清库并重播种当前场景">重置演示</button>
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
              <button disabled={!ready} onClick={startDraw} title="在地图上点多个顶点画该类型区域，≥3 点后点完成">绘制「{kindLabel(drawKind)}」</button>
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
          <span><i style={{ background: '#ffffff', border: '1px solid #bbb' }} />活动区</span>
          <span><i style={{ background: '#f59e0b' }} />搜索区</span>
          <span><i style={{ background: '#3b82f6' }} />防护区</span>
          <span><i style={{ background: '#ef4444' }} />禁入区</span>
          <span><i style={{ background: '#14b8a6' }} />安全区</span>
          <span><i style={{ background: '#f59e0b', borderRadius: '50%' }} />发现</span>
          <span><i style={{ background: '#db2777', borderRadius: '50%' }} />变化</span>
          {scenario === 'sar' && <span><i style={{ background: '#dc2626', borderRadius: '50%' }} />目标</span>}
          {scenario === 'sar' && <span><i style={{ background: '#6b7280', borderRadius: '50%' }} />疑似</span>}
          {scenario === 'sar' && <span><i style={{ background: '#f97316' }} />热点区</span>}
        </div>

        <div className="msg">{msg}</div>
      </div>

      {det && (
        <div className="det-card">
          <b>发现点 #{det.id}</b>
          <div>类别：{det.label} · 置信度 {Number(det.confidence).toFixed(2)}
            {det.priority > 0 && <> · 优先级 <b>{bandOf(det.priority)}</b>({det.priority})</>}</div>
          <div>状态：{det.status} · {String(det.simulated) === 'true' ? '模拟/预置' : '真实推理'}</div>
          {scenario === 'sar' && det.priority > 0 && (
            <div className="prio-set">
              <span>改优先级</span>
              {['P0', 'P1', 'P2', 'P3'].map((b) => (
                <button key={b} className={bandOf(det.priority) === b ? 'active' : ''}
                  onClick={() => setPrio(PRIO_SCORE[b])}>{b}</button>
              ))}
            </div>
          )}
          {scenario === 'sar' && (
            <button className="arrive" onClick={arriveAt}>到达核查（是否真目标）</button>
          )}
          <div className="det-actions">
            <button className="ok" onClick={() => reviewDet('confirmed')}>确认</button>
            <button className="no" onClick={() => reviewDet('rejected')}>驳回</button>
            <button onClick={() => setDet(null)}>关闭</button>
          </div>
        </div>
      )}

      {droneView && (
        <div className="drone-view">
          <div className="dv-head">
            <span>🚁 无人机视角 · {droneView.label}</span>
            <button onClick={() => setDroneView(null)} title="关闭">×</button>
          </div>
          <div ref={dvMapEl} className="dv-map" />
          <div className="dv-cap">{droneView.lat.toFixed(5)}, {droneView.lon.toFixed(5)} · 卫星超分(FSRCNN×4)·滚轮缩放·模拟非真实无人机影像</div>
        </div>
      )}
    </div>
  )
}
