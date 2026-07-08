/* Standalone prototype: GE-style photorealistic 3D flythrough over rural /
 * suburban North Rhine-Westphalia (NRW), streamed live from the open
 * NRW 3D-Mesh I3S service (10 cm textured reality mesh, Datenlizenz DE Zero 2.0
 * — effectively public domain, no key, no download).
 *
 * Renderer: deck.gl Tile3DLayer + loaders.gl I3SLoader. This is decoupled from
 * the MapLibre main app (MapLibre cannot render 3D Tiles / I3S natively).
 */
import { createRoot } from 'react-dom/client'
import { useState, useCallback } from 'react'
import DeckGL from '@deck.gl/react'
import { FlyToInterpolator } from '@deck.gl/core'
import { Tile3DLayer } from '@deck.gl/geo-layers'
import { I3SLoader } from '@loaders.gl/i3s'

// I3S IntegratedMesh scene layer (verified live: ACAO:* so it streams in-browser)
const SCENE = 'https://www.gis.nrw.de/geobasis/3D_mesh/SceneServer/layers/0'

// rural / suburban vantage points inside NRW (SAR-relevant terrain), + one city
const SPOTS = [
  { key: 'eifel', name: 'Eifel 森林 (Monschau)', longitude: 6.2536, latitude: 50.5548 },
  { key: 'muenster', name: 'Münsterland 农田 (Billerbeck)', longitude: 7.2946, latitude: 51.9793 },
  { key: 'sauerland', name: 'Sauerland 森林 (Winterberg)', longitude: 8.5306, latitude: 51.1951 },
  { key: 'koeln', name: 'Köln 城区 (对比)', longitude: 6.9578, latitude: 50.9413 },
]

const INITIAL = {
  longitude: SPOTS[0].longitude, latitude: SPOTS[0].latitude,
  zoom: 16.5, pitch: 65, bearing: 20, maxPitch: 85,
}

function App() {
  const [viewState, setViewState] = useState(INITIAL)
  const [status, setStatus] = useState('连接 NRW 3D-Mesh…（首次拉取瓦片需几秒）')
  const [tiles, setTiles] = useState(0)

  const flyTo = useCallback((s) => {
    setViewState((v) => ({
      ...v, longitude: s.longitude, latitude: s.latitude, zoom: 16.5, pitch: 65,
      transitionDuration: 2500, transitionInterpolator: new FlyToInterpolator({ curve: 1.4 }),
    }))
    setStatus(`飞往 ${s.name}…`)
  }, [])

  const layer = new Tile3DLayer({
    id: 'nrw-mesh',
    data: SCENE,
    loader: I3SLoader,
    onTilesetLoad: () => setStatus('已连接 · 左键拖动旋转/倾斜 · 滚轮缩放 · 右键平移'),
    onTileLoad: () => setTiles((n) => n + 1),
    onTileError: (_t, _url, message) => setStatus('瓦片错误：' + message),
  })

  return (
    <>
      <DeckGL
        viewState={viewState}
        onViewStateChange={(e) => setViewState(e.viewState)}
        controller={{ maxPitch: 85, inertia: true }}
        layers={[layer]}
        parameters={{ clearColor: [0.04, 0.07, 0.11, 1] }}
      />
      <div className="hud">
        <div className="title">🌄 NRW 3D 实景无人机预览
          <span>deck.gl + I3S · 10cm 实景网格 · 公共领域(DL-DE Zero 2.0)</span>
        </div>
        <div className="spots">
          {SPOTS.map((s) => (
            <button key={s.key} onClick={() => flyTo(s)}>{s.name}</button>
          ))}
        </div>
        <div className="status">
          {status} · 瓦片 {tiles} ·{' '}
          <a className="back" href="/index.html">← 返回主界面</a>
        </div>
      </div>
    </>
  )
}

createRoot(document.getElementById('root')).render(<App />)
