-- =============================================
-- NEXOR ERP Migration 0010 - Recete Maliyet Bilesenleri
-- =============================================
-- Her recete (kaplama.plc_recete_tanimlari) icin standart maliyet bilesenleri.
-- Birim parca basina:
--   Hammadde fiyati x tuketim
-- + Iscilik saat ucreti x cevrim suresi / aski kapasitesi
-- + Enerji kWh x sure x birim fiyat
-- + Kimyasal kg x birim fiyat
-- + MOH (Genel Uretim Gideri) yuzdesi
-- =============================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'maliyet')
    EXEC('CREATE SCHEMA maliyet');
GO

-- 1) Recete maliyet bilesenleri (versiyonlu - tarihe gore aktif kayit)
IF NOT EXISTS (
    SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'maliyet' AND t.name = 'recete_bilesenleri'
)
BEGIN
    CREATE TABLE maliyet.recete_bilesenleri (
        id                    BIGINT IDENTITY(1,1) PRIMARY KEY,
        recete_no             INT          NOT NULL,
        gecerlilik_baslangic  DATE         NOT NULL DEFAULT CAST(GETDATE() AS DATE),
        gecerlilik_bitis      DATE         NULL,        -- NULL = halen aktif
        para_birimi           NVARCHAR(10) NOT NULL DEFAULT 'TRY',

        -- HAMMADDE
        -- Genelde kaplama sektorunde "1 parca / 1 askı" basina malzeme tuketimi
        -- Bu bir egzotik degisken: bazi receteler hammadde tuketmez (yalnizca kaplama)
        hammadde_birim_fiyat       DECIMAL(15, 4) NOT NULL DEFAULT 0,  -- TL/kg
        hammadde_tuketim_kg        DECIMAL(15, 4) NOT NULL DEFAULT 0,  -- kg/parca

        -- ISCILIK
        -- Operatör saat ucreti x cevrim suresi / 1 askıdaki parca sayısı
        iscilik_saat_ucreti        DECIMAL(15, 4) NOT NULL DEFAULT 0,  -- TL/saat (operator)
        iscilik_kisi_sayisi        DECIMAL(5, 2)  NOT NULL DEFAULT 1,  -- ayni anda calisan
        aski_parca_kapasitesi      INT            NOT NULL DEFAULT 1,  -- 1 askıdaki parca

        -- ENERJI
        enerji_kwh_per_saat        DECIMAL(15, 4) NOT NULL DEFAULT 0,  -- kazan ortalama kWh
        enerji_birim_fiyat         DECIMAL(15, 4) NOT NULL DEFAULT 0,  -- TL/kWh
        -- Cevrim suresi recete tanimindaki toplam_sure_dk'dan alinir

        -- KIMYASAL
        kimyasal_tuketim_kg        DECIMAL(15, 4) NOT NULL DEFAULT 0,  -- kg/parca (banyo tuketimi)
        kimyasal_birim_fiyat       DECIMAL(15, 4) NOT NULL DEFAULT 0,  -- TL/kg

        -- MOH (Manufacturing Overhead - Genel Uretim Gideri)
        moh_yuzde                  DECIMAL(5, 2)  NOT NULL DEFAULT 0,  -- DM+DL+Enerji+Kim toplaminin %X kadari
        moh_sabit_tutar            DECIMAL(15, 4) NOT NULL DEFAULT 0,  -- alternatif: parca basina sabit (TL)

        -- KAR MARJI hedefi (teklif icin)
        kar_marj_yuzde             DECIMAL(5, 2)  NOT NULL DEFAULT 0,  -- 0=satilan fiyatla aynidir

        notlar                     NVARCHAR(500) NULL,

        olusturma_tarihi           DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        olusturan_id               BIGINT NULL,
        guncelleme_tarihi          DATETIME2 NULL,
        guncelleyen_id             BIGINT NULL,

        CONSTRAINT FK_recete_bilesen_recete
            FOREIGN KEY (recete_no) REFERENCES kaplama.plc_recete_tanimlari(recete_no)
    );

    -- Bir recete icin bir donemde sadece 1 aktif kayit olmali
    CREATE UNIQUE INDEX UX_recete_bilesen_aktif
        ON maliyet.recete_bilesenleri (recete_no, gecerlilik_baslangic);
    CREATE INDEX IX_recete_bilesen_aktif
        ON maliyet.recete_bilesenleri (recete_no) WHERE gecerlilik_bitis IS NULL;

    PRINT 'maliyet.recete_bilesenleri tablosu olusturuldu';
END
ELSE
    PRINT 'maliyet.recete_bilesenleri zaten mevcut';
GO

-- 2) Hesaplanmis (cached) recete maliyet snapshot - sik sorulan rapor icin
IF NOT EXISTS (
    SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'maliyet' AND t.name = 'recete_maliyet_cache'
)
BEGIN
    CREATE TABLE maliyet.recete_maliyet_cache (
        recete_no              INT          NOT NULL PRIMARY KEY,
        recete_adi             NVARCHAR(200) NULL,
        cevrim_suresi_dk       DECIMAL(10, 2) NULL,

        -- Bilesen bazli birim parca maliyet (TL)
        m_hammadde             DECIMAL(15, 4) NOT NULL DEFAULT 0,
        m_iscilik              DECIMAL(15, 4) NOT NULL DEFAULT 0,
        m_enerji               DECIMAL(15, 4) NOT NULL DEFAULT 0,
        m_kimyasal             DECIMAL(15, 4) NOT NULL DEFAULT 0,
        m_moh                  DECIMAL(15, 4) NOT NULL DEFAULT 0,
        m_toplam               DECIMAL(15, 4) NOT NULL DEFAULT 0,
        m_satis_onerisi        DECIMAL(15, 4) NOT NULL DEFAULT 0,  -- toplam x (1 + kar_marj)

        para_birimi            NVARCHAR(10) NOT NULL DEFAULT 'TRY',
        son_hesap_tarihi       DATETIME2 NOT NULL DEFAULT SYSDATETIME(),
        bilesen_id             BIGINT NULL  -- Hesapta kullanilan kaynak satir
    );

    PRINT 'maliyet.recete_maliyet_cache tablosu olusturuldu';
END
ELSE
    PRINT 'maliyet.recete_maliyet_cache zaten mevcut';
GO
