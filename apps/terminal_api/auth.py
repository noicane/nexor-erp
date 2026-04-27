# -*- coding: utf-8 -*-
"""
NEXOR Terminal API - JWT + Kart/PIN Auth

Kart girisi: USB kart okuyucu kart_id'si veya PDKS sicil. Esleme NEXOR mantigiyla
(`sistem.kullanicilar.kart_id` ya da `ik.personeller.kart_id`/`kart_no`/`sicil_no`).

PIN girisi: kullanici_adi + 4 haneli PIN. PIN ya `sistem.kullanicilar.terminal_pin`
kolonunda saklanir (varsa) ya da yoksa fallback olarak `sifre_hash` kullanilmaz
(guvenlik nedeniyle, ayri PIN sistemi tercih). Migration ile kolon eklenmeli.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import JWT_ALGORITHM, JWT_EXPIRES_HOURS, JWT_SECRET
from .db import fetch_one


_security = HTTPBearer(auto_error=False)


# ============================================================================
# JWT
# ============================================================================

def _create_token(kullanici_id: int, kullanici_adi: str, ad_soyad: str = "") -> str:
    payload = {
        "sub": str(kullanici_id),
        "kullanici_adi": kullanici_adi,
        "ad_soyad": ad_soyad,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRES_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Oturum suresi doldu")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Gecersiz token")


# ============================================================================
# DB Lookup
# ============================================================================

def _lookup_by_kart(kart_id: str) -> Optional[dict]:
    """Kart numarasi ile kullanici bul. NEXOR'daki ayni 7-seviyeli mantik (kisaltilmis)."""
    if not kart_id:
        return None
    kart = kart_id.strip()
    # 1) sistem.kullanicilar.kart_id (USB okuyucu numarasi)
    row = fetch_one("""
        SELECT k.id, k.kullanici_adi, ISNULL(p.ad + ' ' + p.soyad, k.kullanici_adi) AS ad_soyad
        FROM sistem.kullanicilar k
        LEFT JOIN ik.personeller p ON p.id = k.personel_id
        WHERE k.kart_id = ? AND k.aktif_mi = 1 AND k.silindi_mi = 0
    """, kart)
    if row:
        return row
    # 2) ik.personeller.kart_id veya kart_no esleme (PDKS cihazi numarasi farkli olabilir)
    row = fetch_one("""
        SELECT k.id, k.kullanici_adi, p.ad + ' ' + p.soyad AS ad_soyad
        FROM ik.personeller p
        INNER JOIN sistem.kullanicilar k ON k.personel_id = p.id
        WHERE (p.kart_id = ? OR p.kart_no = ? OR p.sicil_no = ?)
          AND k.aktif_mi = 1 AND k.silindi_mi = 0
    """, kart, kart, kart)
    return row


def _lookup_by_username(kullanici_adi: str) -> Optional[dict]:
    if not kullanici_adi:
        return None
    return fetch_one("""
        SELECT k.id, k.kullanici_adi,
               ISNULL(p.ad + ' ' + p.soyad, k.kullanici_adi) AS ad_soyad,
               k.terminal_pin_hash, k.terminal_pin_set
        FROM sistem.kullanicilar k
        LEFT JOIN ik.personeller p ON p.id = k.personel_id
        WHERE k.kullanici_adi = ? AND k.aktif_mi = 1 AND k.silindi_mi = 0
    """, kullanici_adi.strip())


# ============================================================================
# PIN Hash
# ============================================================================

def hash_pin(kullanici_id: int, pin: str) -> str:
    """PIN'i kullanici ID + sabit salt ile SHA-256 hashle.

    Bcrypt overhead'i mobil terminal'de gereksiz (PIN zaten 4 hane); per-kullanici
    salt ile rainbow attack onlenir, brute force icin lockout backend'de yapilir.
    """
    salt = f"nexor-terminal-pin-v1::{kullanici_id}::"
    return hashlib.sha256((salt + pin).encode("utf-8")).hexdigest()


# ============================================================================
# Public API
# ============================================================================

def login_with_kart(kart_id: str) -> dict:
    """Kart ile giris."""
    user = _lookup_by_kart(kart_id)
    if not user:
        raise HTTPException(status_code=401, detail="Kart taninmiyor")
    token = _create_token(user["id"], user["kullanici_adi"], user.get("ad_soyad") or "")
    return {
        "token": token,
        "kullanici_id": user["id"],
        "kullanici_adi": user["kullanici_adi"],
        "ad_soyad": user.get("ad_soyad") or "",
    }


def login_with_pin(kullanici_adi: str, pin: str) -> dict:
    """Kullanici adi + 4 haneli PIN ile giris."""
    if not pin or not pin.isdigit() or len(pin) not in (4, 6):
        raise HTTPException(status_code=400, detail="PIN 4 veya 6 haneli rakam olmali")
    user = _lookup_by_username(kullanici_adi)
    if not user:
        raise HTTPException(status_code=401, detail="Kullanici bulunamadi")
    if not user.get("terminal_pin_set"):
        raise HTTPException(
            status_code=403,
            detail="Bu kullanicinin terminal PIN'i tanimli degil. Yoneticiye basvurun."
        )
    expected = user.get("terminal_pin_hash") or ""
    if hash_pin(user["id"], pin) != expected:
        raise HTTPException(status_code=401, detail="PIN hatali")
    token = _create_token(user["id"], user["kullanici_adi"], user.get("ad_soyad") or "")
    return {
        "token": token,
        "kullanici_id": user["id"],
        "kullanici_adi": user["kullanici_adi"],
        "ad_soyad": user.get("ad_soyad") or "",
    }


# ============================================================================
# Dependency: aktif kullaniciyi token'dan cikar
# ============================================================================

def current_user(creds: HTTPAuthorizationCredentials = Depends(_security)) -> dict:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer token gerekli")
    payload = _decode_token(creds.credentials)
    return {
        "id": int(payload.get("sub", 0)),
        "kullanici_adi": payload.get("kullanici_adi", ""),
        "ad_soyad": payload.get("ad_soyad", ""),
    }
