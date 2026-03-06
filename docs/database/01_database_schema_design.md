# ATMO LOGIC ERP - VERİTABANI ŞEMASI TASARIMI

## Genel Bilgiler

- **Veritabanı:** SQL Server 2019+
- **Karakter Seti:** UTF-8 (Turkish_CI_AS collation)
- **Naming Convention:** snake_case

---

## ORTAK ALANLAR (Tüm tablolarda)

```sql
-- Audit alanları (her tabloda olacak)
id                  BIGINT IDENTITY(1,1) PRIMARY KEY
uuid                UNIQUEIDENTIFIER DEFAULT NEWID() NOT NULL
created_at          DATETIME2 DEFAULT GETDATE() NOT NULL
updated_at          DATETIME2 DEFAULT GETDATE() NOT NULL
created_by          BIGINT NOT NULL  -- FK to users
updated_by          BIGINT NOT NULL  -- FK to users
is_deleted          BIT DEFAULT 0 NOT NULL
deleted_at          DATETIME2 NULL
deleted_by          BIGINT NULL
```

---

## ŞEMA 1: lookup (Sabit Tanımlar)

### lookup.coating_types (Kaplama Türleri)
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGINT | PK |
| code | NVARCHAR(20) | KTF, ZN, ZNNI, TOZ |
| name | NVARCHAR(100) | Kataforez, Çinko, vb. |
| description | NVARCHAR(500) | |
| is_active | BIT | |

### lookup.production_lines (Üretim Hatları)
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGINT | PK |
| code | NVARCHAR(20) | HAT-01, HAT-02 |
| name | NVARCHAR(100) | Kataforez Hattı 1 |
| coating_type_id | BIGINT | FK |
| plc_ip_address | NVARCHAR(50) | S7-1500 IP |
| plc_rack | INT | |
| plc_slot | INT | |
| capacity_per_hour | DECIMAL(10,2) | m²/saat |
| is_active | BIT | |

### lookup.units (Birimler)
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGINT | PK |
| code | NVARCHAR(10) | KG, LT, M2, ADET |
| name | NVARCHAR(50) | |
| category | NVARCHAR(50) | weight, volume, area, count |

### lookup.currencies (Para Birimleri)
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGINT | PK |
| code | NVARCHAR(3) | TRY, USD, EUR |
| symbol | NVARCHAR(5) | ₺, $, € |
| name | NVARCHAR(50) | |

### lookup.countries (Ülkeler)
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGINT | PK |
| code | NVARCHAR(3) | TR, DE, US |
| name | NVARCHAR(100) | |

### lookup.cities (Şehirler)
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGINT | PK |
| country_id | BIGINT | FK |
| code | NVARCHAR(10) | 34, 16 |
| name | NVARCHAR(100) | İstanbul, Bursa |

### lookup.defect_types (Hata Türleri)
| Kolon | Tip | Açıklama |
|-------|-----|----------|
| id | BIGINT | PK |
| code | NVARCHAR(20) | |
| name | NVARCHAR(100) | Kabarcık