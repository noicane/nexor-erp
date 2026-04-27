# -*- coding: utf-8 -*-
"""
NEXOR Terminal API - Konfigurasyon
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# JWT
JWT_SECRET = os.environ.get("TERMINAL_JWT_SECRET", "change-me-in-production-32-bytes-minimum-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRES_HOURS = int(os.environ.get("TERMINAL_JWT_EXPIRES_HOURS", "8"))

# API
API_HOST = os.environ.get("TERMINAL_API_HOST", "0.0.0.0")
API_PORT = int(os.environ.get("TERMINAL_API_PORT", "8002"))
API_TITLE = "NEXOR Terminal API"
API_VERSION = "0.1.0"

# CORS - Flutter dev/release ve LAN'daki tum cihazlar
CORS_ORIGINS = ["*"]

# Loglama
LOG_LEVEL = os.environ.get("TERMINAL_LOG_LEVEL", "INFO")
