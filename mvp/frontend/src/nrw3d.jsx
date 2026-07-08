/* Standalone prototype: GE-style photorealistic 3D flythrough over rural /
 * suburban North Rhine-Westphalia (NRW), streamed live from the open NRW
 * 3D-Mesh I3S service (10 cm textured reality mesh, Datenlizenz DE Zero 2.0 —
 * public domain, no key, no download).
 *
 * Renderer: CesiumJS I3SDataProvider. Cesium's I3S support was built with Esri
 * to consume production scene layers (often in a projected CRS like this one's
 * ETRS89/UTM32 = EPSG:25832), so it should georeference the mesh where deck.gl's
 * loader could not. Decoupled from the MapLibre main app.
 */
import * as Cesium from 'cesium'
import 'cesium/Build/Cesium/Widgets/widgets.css'

// I3S IntegratedMesh scene service (root URL). Verified live, ACAO:*.
const SCENE = 'https://www.gis.nrw.de/geobasis/3D_mesh/SceneServer'

// rural / suburban vantage points inside NRW (SAR-relevant terrain) + one city
const SPOTS = [
  { name: 'Eifel 森林 (Monschau)', lon: 6.2536, lat: 50.5548 },
  { name: 'Münsterland 农田 (Billerbeck)', lon: 7.2946, lat: 51.9793 },
  { name: 'Sauerland 森林 (Winterberg)', lon: 8.5306, lat: 51.1951 },
  { name: 'Köln 城区 (对比)', lon: 6.9578, lat: 50.9413 },
]

const statusEl = document.getElementById('status')
const meshEl = document.getElementById('mesh')
const spotsEl = document.getElementById('spots')
const setStatus = (t) => { statusEl.innerHTML = t + ' · <a class="back" href="/index.html">← 返回主界面</a>' }
const setMesh = (t) => { meshEl.textContent = t }

// No Cesium ion (avoid needing a token): OSM imagery + plain ellipsoid globe.
Cesium.Ion.defaultAccessToken = undefined
const viewer = new Cesium.Viewer('cesiumContainer', {
  baseLayerPicker: false, geocoder: false, homeButton: false, sceneModePicker: false,
  animation: false, timeline: false, navigationHelpButton: false, infoBox: false,
  selectionIndicator: false, fullscreenButton: false,
  terrainProvider: new Cesium.EllipsoidTerrainProvider(),
})
viewer.imageryLayers.removeAll()
viewer.imageryLayers.addImageryProvider(
  new Cesium.OpenStreetMapImageryProvider({ url: 'https://tile.openstreetmap.org/' }))
viewer.scene.globe.show = true

function flyTo(s, altitude = 900) {
  setStatus(`飞往 ${s.name}…`)
  viewer.camera.flyTo({
    destination: Cesium.Cartesian3.fromDegrees(s.lon, s.lat, altitude),
    orientation: { heading: Cesium.Math.toRadians(20), pitch: Cesium.Math.toRadians(-35), roll: 0 },
    duration: 2.5,
  })
}

for (const s of SPOTS) {
  const b = document.createElement('button')
  b.textContent = s.name
  b.onclick = () => flyTo(s)
  spotsEl.appendChild(b)
}

setStatus('左键拖旋转 · 右键/滚轮缩放 · 中键倾斜')
setMesh('网格：连接中…（首次几秒）')
;(async () => {
  try {
    const provider = await Cesium.I3SDataProvider.fromUrl(SCENE)
    viewer.scene.primitives.add(provider)
    // report the mesh's ACTUAL coverage, and fly to where the data really is
    const ext = provider.extent
    if (ext) {
      const w = Cesium.Math.toDegrees(ext.west), s = Cesium.Math.toDegrees(ext.south)
      const e = Cesium.Math.toDegrees(ext.east), n = Cesium.Math.toDegrees(ext.north)
      const clon = (w + e) / 2, clat = (s + n) / 2
      console.log('I3S extent (deg):', { w, s, e, n }, 'sublayers:', provider.sublayers?.length)
      setMesh(`✅ 网格已连接 · 覆盖 ${w.toFixed(2)},${s.toFixed(2)} → ${e.toFixed(2)},${n.toFixed(2)}`)
      viewer.camera.flyTo({
        destination: Cesium.Cartesian3.fromDegrees(clon, clat, 3500),
        orientation: { heading: 0, pitch: Cesium.Math.toRadians(-40), roll: 0 }, duration: 3,
      })
    } else {
      setMesh('✅ 网格已连接（无 extent 信息，尝试取景点）')
      flyTo(SPOTS[3], 1500)   // Köln — most likely to be in the published set
    }
  } catch (err) {
    console.error('I3S load failed:', err)
    setMesh('❌ 网格加载失败：' + (err && err.message ? err.message : err))
  }
})()
