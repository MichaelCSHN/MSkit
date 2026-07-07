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


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
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


@app.get("/")
def root():
    return {"name": "MSkit MVP API", "docs": "/docs", "api": "/api"}
