# -*- coding: utf-8 -*-
r"""
NEXOR Terminal API - FastAPI Ana Uygulama

Calistirma:
    apps\terminal_api> ..\..\venv\Scripts\activate
    apps\terminal_api> uvicorn apps.terminal_api.main:app --host 0.0.0.0 --port 8002

Veya:
    apps\terminal_api\run.bat
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import API_TITLE, API_VERSION, CORS_ORIGINS, LOG_LEVEL
from .routers import auth_router, sevk_yeni_router

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("terminal_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NEXOR Terminal API baslatildi (v%s)", API_VERSION)
    yield
    logger.info("NEXOR Terminal API kapaniyor")


app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="EDA51 ve tablet uygulamasi icin REST API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routerlar
app.include_router(auth_router.router)
app.include_router(sevk_yeni_router.router)


@app.get("/", tags=["meta"])
def root():
    return {
        "service": API_TITLE,
        "version": API_VERSION,
        "endpoints": [
            "/auth/kart", "/auth/pin", "/auth/me",
            "/sevk-yeni/arac-bilgileri", "/sevk-yeni/hazir-urunler",
            "/sevk-yeni/lot-dogrula", "/sevk-yeni/olustur",
            "/docs",
        ],
    }


@app.get("/health", tags=["meta"])
def health():
    """DB ping ile saglik kontrolu."""
    try:
        from .db import fetch_one
        row = fetch_one("SELECT 1 AS ok")
        return {"status": "ok", "db": bool(row and row.get("ok") == 1)}
    except Exception as e:
        return {"status": "degraded", "db": False, "error": str(e)[:200]}
