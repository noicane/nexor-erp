# -*- coding: utf-8 -*-
"""
NEXOR Terminal API - Auth Router
"""
from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field

from ..auth import current_user, login_with_kart, login_with_pin

router = APIRouter(prefix="/auth", tags=["auth"])


class KartLoginInput(BaseModel):
    kart_id: str = Field(..., min_length=2, max_length=50)


class PinLoginInput(BaseModel):
    kullanici_adi: str = Field(..., min_length=2, max_length=80)
    pin: str = Field(..., min_length=4, max_length=6)


class LoginResult(BaseModel):
    token: str
    kullanici_id: int
    kullanici_adi: str
    ad_soyad: str


class MeResult(BaseModel):
    id: int
    kullanici_adi: str
    ad_soyad: str


@router.post("/kart", response_model=LoginResult, summary="Kart ile giris")
def kart_login(payload: KartLoginInput):
    """USB kart okuyucudan gelen kart_id ile login."""
    return login_with_kart(payload.kart_id)


@router.post("/pin", response_model=LoginResult, summary="Kullanici + PIN giris")
def pin_login(payload: PinLoginInput):
    """4 veya 6 haneli PIN ile login (kart yedek)."""
    return login_with_pin(payload.kullanici_adi, payload.pin)


@router.get("/me", response_model=MeResult, summary="Aktif oturum bilgisi")
def me(user: dict = Depends(current_user)):
    return MeResult(
        id=user["id"],
        kullanici_adi=user["kullanici_adi"],
        ad_soyad=user["ad_soyad"],
    )
