-- ============================================
-- NEXOR ERP - Teklif Modulu Veritabani Tablolari
-- Schema: satislar
-- Tarih: 2026-02-16
-- ============================================

-- Schema olustur (yoksa)
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'satislar')
    EXEC('CREATE SCHEMA satislar')
GO

-- ============================================
-- 1. ANA TEKLIF TABLOSU
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'satislar.teklifler') AND type = 'U')
BEGIN
    CREATE TABLE satislar.teklifler (
        id                      INT IDENTITY(1,1) PRIMARY KEY,
        uuid                    UNIQUEIDENTIFIER DEFAULT NEWID() NOT NULL,
        teklif_no               NVARCHAR(20) NOT NULL,
        revizyon_no             INT DEFAULT 0 NOT NULL,
        revizyon_kodu           AS (N'Rev.' + RIGHT('00' + CAST(revizyon_no AS NVARCHAR), 2)),
        ana_teklif_id           INT NULL,

        -- Tarihler
        tarih                   DATE DEFAULT GETDATE() NOT NULL,
        gecerlilik_tarihi       DATE NULL,

        -- Cari bilgileri
        cari_id                 INT NULL,
        cari_unvani             NVARCHAR(250) NULL,
        cari_yetkili            NVARCHAR(100) NULL,
        cari_telefon            NVARCHAR(30) NULL,
        cari_email              NVARCHAR(100) NULL,

        -- Fiyat bilgileri
        ara_toplam              DECIMAL(18,2) DEFAULT 0,
        iskonto_oran            DECIMAL(5,2) DEFAULT 0,
        iskonto_tutar           DECIMAL(18,2) DEFAULT 0,
        kdv_oran                DECIMAL(5,2) DEFAULT 20,
        kdv_tutar               DECIMAL(18,2) DEFAULT 0,
        genel_toplam            DECIMAL(18,2) DEFAULT 0,
        para_birimi             NVARCHAR(5) DEFAULT N'TRY',

        -- Durum
        durum                   NVARCHAR(30) DEFAULT N'TASLAK',
        -- TASLAK, GONDERILDI, ONAYLANDI, REDDEDILDI, IPTAL, IS_EMRINE_DONUSTURULDU

        -- Ek bilgiler
        referans_no             NVARCHAR(50) NULL,
        proje_adi               NVARCHAR(200) NULL,
        teslim_suresi           NVARCHAR(100) NULL,
        odeme_kosullari         NVARCHAR(200) NULL,
        notlar                  NVARCHAR(MAX) NULL,
        ozel_kosullar           NVARCHAR(MAX) NULL,

        -- Is emri iliskisi
        is_emri_id              INT NULL,
        is_emrine_donus_tarihi  DATETIME NULL,

        -- Sablon iliskisi
        sablon_id               INT NULL,

        -- Audit
        olusturma_tarihi        DATETIME DEFAULT GETDATE(),
        guncelleme_tarihi       DATETIME NULL,
        olusturan_id            INT NULL,
        guncelleyen_id          INT NULL,
        silindi_mi              BIT DEFAULT 0,

        -- Foreign keys
        CONSTRAINT FK_teklifler_ana_teklif FOREIGN KEY (ana_teklif_id) REFERENCES satislar.teklifler(id),
    );

    CREATE INDEX IX_teklifler_teklif_no ON satislar.teklifler(teklif_no);
    CREATE INDEX IX_teklifler_cari_id ON satislar.teklifler(cari_id);
    CREATE INDEX IX_teklifler_durum ON satislar.teklifler(durum);
    CREATE INDEX IX_teklifler_tarih ON satislar.teklifler(tarih);
    CREATE INDEX IX_teklifler_ana_teklif ON satislar.teklifler(ana_teklif_id);
END
GO

-- ============================================
-- 2. TEKLIF SATIRLARI TABLOSU
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'satislar.teklif_satirlari') AND type = 'U')
BEGIN
    CREATE TABLE satislar.teklif_satirlari (
        id                      INT IDENTITY(1,1) PRIMARY KEY,
        uuid                    UNIQUEIDENTIFIER DEFAULT NEWID() NOT NULL,
        teklif_id               INT NOT NULL,
        satir_no                INT DEFAULT 1,

        -- Urun bilgileri
        urun_id                 INT NULL,
        stok_kodu               NVARCHAR(50) NULL,
        stok_adi                NVARCHAR(250) NULL,

        -- Kaplama bilgileri
        kaplama_tipi_id         INT NULL,
        kaplama_tipi_adi        NVARCHAR(100) NULL,
        kalinlik_mikron         DECIMAL(10,2) NULL,
        malzeme_tipi            NVARCHAR(100) NULL,
        yuzey_alani             DECIMAL(18,4) NULL,
        yuzey_birimi            NVARCHAR(10) DEFAULT N'dm2',

        -- Miktar ve fiyat
        miktar                  DECIMAL(18,2) DEFAULT 0,
        birim                   NVARCHAR(20) DEFAULT N'ADET',
        birim_fiyat             DECIMAL(18,4) DEFAULT 0,
        iskonto_oran            DECIMAL(5,2) DEFAULT 0,
        tutar                   DECIMAL(18,2) DEFAULT 0,

        -- Aciklamalar
        aciklama                NVARCHAR(500) NULL,
        teknik_not              NVARCHAR(500) NULL,

        CONSTRAINT FK_teklif_satirlari_teklif FOREIGN KEY (teklif_id) REFERENCES satislar.teklifler(id) ON DELETE CASCADE,
    );

    CREATE INDEX IX_teklif_satirlari_teklif ON satislar.teklif_satirlari(teklif_id);
END
GO

-- ============================================
-- 3. TEKLIF SABLONLARI TABLOSU
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'satislar.teklif_sablonlari') AND type = 'U')
BEGIN
    CREATE TABLE satislar.teklif_sablonlari (
        id                      INT IDENTITY(1,1) PRIMARY KEY,
        uuid                    UNIQUEIDENTIFIER DEFAULT NEWID() NOT NULL,
        sablon_adi              NVARCHAR(200) NOT NULL,
        aciklama                NVARCHAR(500) NULL,
        varsayilan_kdv_oran     DECIMAL(5,2) DEFAULT 20,
        varsayilan_iskonto_oran DECIMAL(5,2) DEFAULT 0,
        varsayilan_para_birimi  NVARCHAR(5) DEFAULT N'TRY',
        varsayilan_teslim_suresi NVARCHAR(100) NULL,
        varsayilan_odeme_kosullari NVARCHAR(200) NULL,
        varsayilan_gecerlilik_gun INT DEFAULT 30,
        varsayilan_ozel_kosullar NVARCHAR(MAX) NULL,
        aktif_mi                BIT DEFAULT 1,
        olusturma_tarihi        DATETIME DEFAULT GETDATE(),
        guncelleme_tarihi       DATETIME NULL,
    );
END
GO

-- ============================================
-- 4. TEKLIF SABLON SATIRLARI TABLOSU
-- ============================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'satislar.teklif_sablon_satirlari') AND type = 'U')
BEGIN
    CREATE TABLE satislar.teklif_sablon_satirlari (
        id                      INT IDENTITY(1,1) PRIMARY KEY,
        sablon_id               INT NOT NULL,
        satir_no                INT DEFAULT 1,
        kaplama_tipi_adi        NVARCHAR(100) NULL,
        kalinlik_mikron         DECIMAL(10,2) NULL,
        malzeme_tipi            NVARCHAR(100) NULL,
        birim                   NVARCHAR(20) DEFAULT N'ADET',
        varsayilan_birim_fiyat  DECIMAL(18,4) DEFAULT 0,
        aciklama                NVARCHAR(500) NULL,

        CONSTRAINT FK_sablon_satirlari_sablon FOREIGN KEY (sablon_id) REFERENCES satislar.teklif_sablonlari(id) ON DELETE CASCADE,
    );

    CREATE INDEX IX_sablon_satirlari_sablon ON satislar.teklif_sablon_satirlari(sablon_id);
END
GO

-- ============================================
-- 5. STORED PROCEDURE - YENI TEKLIF NO
-- ============================================
IF EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'satislar.sp_yeni_teklif_no') AND type = 'P')
    DROP PROCEDURE satislar.sp_yeni_teklif_no
GO

CREATE PROCEDURE satislar.sp_yeni_teklif_no
    @teklif_no NVARCHAR(20) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @yil NVARCHAR(4) = CAST(YEAR(GETDATE()) AS NVARCHAR);
    DECLARE @prefix NVARCHAR(10) = N'TEK-' + @yil + N'-';
    DECLARE @max_no INT;

    SELECT @max_no = ISNULL(MAX(
        CAST(REPLACE(teklif_no, @prefix, '') AS INT)
    ), 0)
    FROM satislar.teklifler
    WHERE teklif_no LIKE @prefix + '%';

    SET @teklif_no = @prefix + RIGHT('0000' + CAST(@max_no + 1 AS NVARCHAR), 4);
END
GO

-- ============================================
-- 6. VARSAYILAN SABLONLAR
-- ============================================
IF NOT EXISTS (SELECT 1 FROM satislar.teklif_sablonlari WHERE sablon_adi = N'Cinko Kaplama')
BEGIN
    INSERT INTO satislar.teklif_sablonlari (sablon_adi, aciklama, varsayilan_teslim_suresi, varsayilan_odeme_kosullari, varsayilan_ozel_kosullar)
    VALUES
    (N'Cinko Kaplama', N'Standart cinko kaplama teklif sablonu', N'5-7 is gunu', N'30 gun vadeli', N'Fiyatlar KDV harictir. Teslim suresi siparis onayindan itibaren gecerlidir.'),
    (N'Nikel Kaplama', N'Nikel kaplama teklif sablonu', N'7-10 is gunu', N'30 gun vadeli', N'Fiyatlar KDV harictir. Nikel kalinligi spesifikasyona gore uygulanir.'),
    (N'Kataforez Kaplama', N'Kataforez (E-Coat) kaplama teklif sablonu', N'3-5 is gunu', N'30 gun vadeli', N'Fiyatlar KDV harictir. Renk ve kalinlik musteriye gore belirlenir.'),
    (N'Fosfat Kaplama', N'Fosfat kaplama teklif sablonu', N'3-5 is gunu', N'30 gun vadeli', N'Fiyatlar KDV harictir. Cinko fosfat veya mangan fosfat secenegi mevcuttur.');

    -- Sablon satirlari
    INSERT INTO satislar.teklif_sablon_satirlari (sablon_id, satir_no, kaplama_tipi_adi, kalinlik_mikron, malzeme_tipi, birim, varsayilan_birim_fiyat)
    SELECT s.id, 1, N'Cinko', 8, N'Celik', N'KG', 0
    FROM satislar.teklif_sablonlari s WHERE s.sablon_adi = N'Cinko Kaplama';

    INSERT INTO satislar.teklif_sablon_satirlari (sablon_id, satir_no, kaplama_tipi_adi, kalinlik_mikron, malzeme_tipi, birim, varsayilan_birim_fiyat)
    SELECT s.id, 1, N'Nikel', 10, N'Celik', N'KG', 0
    FROM satislar.teklif_sablonlari s WHERE s.sablon_adi = N'Nikel Kaplama';

    INSERT INTO satislar.teklif_sablon_satirlari (sablon_id, satir_no, kaplama_tipi_adi, kalinlik_mikron, malzeme_tipi, birim, varsayilan_birim_fiyat)
    SELECT s.id, 1, N'Kataforez', 20, N'Celik', N'KG', 0
    FROM satislar.teklif_sablonlari s WHERE s.sablon_adi = N'Kataforez Kaplama';

    INSERT INTO satislar.teklif_sablon_satirlari (sablon_id, satir_no, kaplama_tipi_adi, kalinlik_mikron, malzeme_tipi, birim, varsayilan_birim_fiyat)
    SELECT s.id, 1, N'Fosfat', 5, N'Celik', N'KG', 0
    FROM satislar.teklif_sablonlari s WHERE s.sablon_adi = N'Fosfat Kaplama';
END
GO

PRINT 'Teklif tablolari basariyla olusturuldu.'
GO
