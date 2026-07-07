"""Database engine and session helpers (SQLite via SQLModel)."""
from __future__ import annotations

import os
from pathlib import Path
from sqlmodel import SQLModel, Session, create_engine

# Backend root: .../mvp/backend
BACKEND_ROOT = Path(__file__).resolve().parent.parent
DATA_STORE = Path(os.environ.get("MSKIT_DATA_STORE", BACKEND_ROOT / "data_store"))
DATA_STORE.mkdir(parents=True, exist_ok=True)
MEDIA_DIR = DATA_STORE / "media"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = os.environ.get("MSKIT_DB", str(BACKEND_ROOT / "mskit_mvp.db"))
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    # Import models so metadata is registered before create_all.
    from . import models  # noqa: F401
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
