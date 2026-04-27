# NEXOR Terminal API

Honeywell EDA51 el terminali + tablet (kalite) icin FastAPI servisi.

## Kurulum

```bat
cd D:\PROJELER\ALL\NEXOR_CORE_DATA
python -m venv venv
venv\Scripts\activate
pip install -r apps\terminal_api\requirements.txt
```

PIN giris icin DB migration:

```sql
-- 0008_terminal_pin.sql migration_runner ile otomatik calisir.
-- Manuel: sistem.kullanicilar.terminal_pin_* kolonlari eklenir.
```

## Calistirma

```bat
apps\terminal_api\run.bat
```

API: http://localhost:8002
Swagger UI: http://localhost:8002/docs

## Endpointler

### Auth
- `POST /auth/kart` — `{kart_id}` -> JWT
- `POST /auth/pin` — `{kullanici_adi, pin}` -> JWT
- `GET /auth/me` — Bearer token ile aktif oturum

### Sevkiyat
- `GET /sevk/acik?arama=...` — durum=HAZIRLANDI irsaliyeler
- `GET /sevk/{id}` — irsaliye detay + satirlar (lot durumu ile)
- `POST /sevk/{id}/lot-tara` — `{lot_no}` -> match check
- `POST /sevk/{id}/yukle?zorla=false` — durum=SEVK_EDILDI
- `DELETE /sevk/{id}/cache` — okutma cache'i temizle (debug)

## Konfigurasyon (.env)

```env
TERMINAL_JWT_SECRET=...        # Min 32 byte rastgele
TERMINAL_JWT_EXPIRES_HOURS=8
TERMINAL_API_HOST=0.0.0.0
TERMINAL_API_PORT=8002
```

## Mimari

- DB baglantisi NEXOR'un `core/database.py` -> `get_db_connection()` uzerinden gider.
- Lot okutma cache'i in-memory `_okutulan` dict'inde tutulur. Restart'ta silinir.
  Production'da `sevkiyat.terminal_okutma_log` tablosuna persistance gerekir.
- Token JWT (HS256), 8 saat omurlu varsayilan.
- PIN: SHA-256 + per-kullanici salt. 4 veya 6 hane.

## Mobile Side

Flutter uygulamasi `apps/nexor_terminal/` altinda (ayri scaffold).
