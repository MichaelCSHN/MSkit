"""Self-contained Real-ESRGAN x4 (no basicsr/realesrgan packages).

Uses the lightweight `realesr-general-x4v3` model (SRVGGNetCompact) — small
(~5MB), CPU-friendly, and much sharper than FSRCNN. Architecture is inlined so
we only depend on `torch`. Weights auto-download on first use.
"""
from __future__ import annotations

import urllib.request
from PIL import Image

from .db import DATA_STORE

_MODEL_URL = ("https://github.com/xinntao/Real-ESRGAN/releases/download/"
              "v0.2.5.0/realesr-general-x4v3.pth")
_MODEL_PATH = DATA_STORE / "models" / "realesr-general-x4v3.pth"
_upscaler = None   # cached callable(pil)->pil, or False if unavailable


def _build_net():
    import torch
    from torch import nn
    from torch.nn import functional as F

    class SRVGGNetCompact(nn.Module):
        """Compact SR VGG net (Real-ESRGAN general-x4v3)."""
        def __init__(self, num_in_ch=3, num_out_ch=3, num_feat=64, num_conv=32, upscale=4):
            super().__init__()
            self.upscale = upscale
            self.body = nn.ModuleList()
            self.body.append(nn.Conv2d(num_in_ch, num_feat, 3, 1, 1))
            self.body.append(nn.PReLU(num_parameters=num_feat))
            for _ in range(num_conv):
                self.body.append(nn.Conv2d(num_feat, num_feat, 3, 1, 1))
                self.body.append(nn.PReLU(num_parameters=num_feat))
            self.body.append(nn.Conv2d(num_feat, num_out_ch * upscale * upscale, 3, 1, 1))
            self.upsampler = nn.PixelShuffle(upscale)

        def forward(self, x):
            out = x
            for layer in self.body:
                out = layer(out)
            out = self.upsampler(out)
            out = out + F.interpolate(x, scale_factor=self.upscale, mode="nearest")
            return out

    return SRVGGNetCompact()


def _load():
    global _upscaler
    if _upscaler is not None:
        return _upscaler
    try:
        import torch
        _MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not _MODEL_PATH.exists():
            req = urllib.request.Request(_MODEL_URL, headers={"User-Agent": "MSkitMVP/0.1"})
            with urllib.request.urlopen(req, timeout=30) as r:
                _MODEL_PATH.write_bytes(r.read())
        net = _build_net()
        sd = torch.load(str(_MODEL_PATH), map_location="cpu")
        sd = sd.get("params", sd.get("params_ema", sd))
        net.load_state_dict(sd, strict=True)
        net.eval()
        torch.set_num_threads(max(1, (torch.get_num_threads() or 4)))

        def upscale(pil: Image.Image) -> Image.Image:
            import numpy as np
            arr = np.asarray(pil.convert("RGB"), dtype="float32") / 255.0
            ten = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0)
            with torch.no_grad():
                out = net(ten)
            out = out.squeeze(0).permute(1, 2, 0).clamp_(0, 1).numpy()
            return Image.fromarray((out * 255.0 + 0.5).astype("uint8"))

        _upscaler = upscale
    except Exception:
        _upscaler = False
    return _upscaler


def upscale4(pil: Image.Image):
    """Return x4 PIL image via Real-ESRGAN, or None if unavailable."""
    fn = _load()
    return fn(pil) if fn else None


def available() -> bool:
    return bool(_load())
