"""MSkit MVP backend entrypoint.

Run (dev):
    uvicorn app.main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import init_db
from .seed import seed_if_empty
from .api import router
from .tiles import router as tiles_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        seeded = seed_if_empty()
    except Exception:
        # schema drift (new columns in an old dev DB): recreate and reseed
        from sqlmodel import SQLModel
        from .db import engine
        SQLModel.metadata.drop_all(engine)
        SQLModel.metadata.create_all(engine)
        seeded = seed_if_empty()
    if seeded:
        print(f"[seed] created demo activity id={seeded}")
    yield


app = FastAPI(title="MSkit MVP API", version="0.1.0", lifespan=lifespan)

# Dev CORS: allow the Vite frontend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(tiles_router, prefix="/api")


@app.get("/")
def root():
    return {"name": "MSkit MVP API", "docs": "/docs", "api": "/api"}
