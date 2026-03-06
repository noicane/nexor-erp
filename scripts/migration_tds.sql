-- ============================================================
-- NEXOR ERP - TDS (Technical Data Sheet) Migration
-- Tarih: 2026-02-19
-- Aciklama: Banyo kartlarina TDS destegi icin 4 yeni tablo
-- ============================================================

-- 1. BANYO TDS ANA KAYIT
IF NOT EXISTS (SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id=s.schema_id WHERE s.name='uretim' AND t.name='banyo_tds')
BEGIN
    CREATE TABLE uretim.banyo_tds (
        id              BIGINT IDENTITY(1,1) PRIMARY KEY,
        banyo_id        BIGINT NOT NULL,
        tds_kodu        NVARCHAR(50) NOT NULL,
        tds_adi         NVARCHAR(200) NOT NULL,
        versiyon        NVARCHAR(20) DEFAULT '1.0',
        gecerlilik_baslangic DATE NULL,
        gecerlilik_bitis     DATE NULL,
        tedarikci       NVARCHAR(200) NULL,
        aktif_mi        BIT DEFAULT 1,
        notlar          NVARCHAR(MAX) NULL,
        olusturma_tarihi DATETIME DEFAULT GETDATE(),
        guncelleme_tarihi DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_banyo_tds_banyo FOREIGN KEY (banyo_id) REFERENCES uretim.banyo_tanimlari(id)
    );
    PRINT 'uretim.banyo_tds tablosu olusturuldu.';
END
ELSE
    PRINT 'uretim.banyo_tds tablosu zaten mevcut.';
GO

-- 2. TDS DOSYALARI
IF NOT EXISTS (SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id=s.schema_id WHERE s.name='uretim' AND t.name='banyo_tds_dosyalar')
BEGIN
    CREATE TABLE uretim.banyo_tds_dosyalar (
        id              BIGINT IDENTITY(1,1) PRIMARY KEY,
        tds_id          BIGINT NOT NULL,
        dosya_adi       NVARCHAR(500) NOT NULL,
        dosya_yolu      NVARCHAR(1000) NOT NULL,
        dosya_tipi      NVARCHAR(20) NULL,
        dosya_boyut     BIGINT NULL,
        kategori        NVARCHAR(20) DEFAULT 'TDS',
        yukleme_tarihi  DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_tds_dosya_tds FOREIGN KEY (tds_id) REFERENCES uretim.banyo_tds(id),
        CONSTRAINT CHK_tds_dosya_kategori CHECK (kategori IN ('TDS', 'SDS', 'COA', 'DIGER'))
    );
    PRINT 'uretim.banyo_tds_dosyalar tablosu olusturuldu.';
END
ELSE
    PRINT 'uretim.banyo_tds_dosyalar tablosu zaten mevcut.';
GO

-- 3. TDS PARAMETRELERI
IF NOT EXISTS (SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id=s.schema_id WHERE s.name='uretim' AND t.name='banyo_tds_parametreler')
BEGIN
    CREATE TABLE uretim.banyo_tds_parametreler (
        id              BIGINT IDENTITY(1,1) PRIMARY KEY,
        tds_id          BIGINT NOT NULL,
        parametre_kodu  NVARCHAR(50) NOT NULL,
        parametre_adi   NVARCHAR(200) NOT NULL,
        birim           NVARCHAR(50) NULL,
        tds_min         DECIMAL(18,4) NULL,
        tds_hedef       DECIMAL(18,4) NULL,
        tds_max         DECIMAL(18,4) NULL,
        tolerans_yuzde  DECIMAL(5,2) DEFAULT 10.00,
        kritik_mi       BIT DEFAULT 0,
        sira_no         INT DEFAULT 0,
        CONSTRAINT FK_tds_param_tds FOREIGN KEY (tds_id) REFERENCES uretim.banyo_tds(id)
    );
    PRINT 'uretim.banyo_tds_parametreler tablosu olusturuldu.';
END
ELSE
    PRINT 'uretim.banyo_tds_parametreler tablosu zaten mevcut.';
GO

-- 4. AI ANALIZ SONUCLARI (CACHE)
IF NOT EXISTS (SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id=s.schema_id WHERE s.name='uretim' AND t.name='banyo_tds_ai_analiz')
BEGIN
    CREATE TABLE uretim.banyo_tds_ai_analiz (
        id              BIGINT IDENTITY(1,1) PRIMARY KEY,
        banyo_id        BIGINT NOT NULL,
        tds_id          BIGINT NULL,
        analiz_tarihi   DATETIME DEFAULT GETDATE(),
        analiz_tipi     NVARCHAR(50) NOT NULL,
        sonuc_json      NVARCHAR(MAX) NULL,
        ozet            NVARCHAR(MAX) NULL,
        risk_seviyesi   NVARCHAR(20) DEFAULT 'NORMAL',
        oneriler        NVARCHAR(MAX) NULL,
        ai_model        NVARCHAR(50) DEFAULT 'rule_based',
        CONSTRAINT FK_tds_ai_banyo FOREIGN KEY (banyo_id) REFERENCES uretim.banyo_tanimlari(id),
        CONSTRAINT FK_tds_ai_tds FOREIGN KEY (tds_id) REFERENCES uretim.banyo_tds(id),
        CONSTRAINT CHK_tds_ai_risk CHECK (risk_seviyesi IN ('NORMAL', 'UYARI', 'KRITIK'))
    );
    PRINT 'uretim.banyo_tds_ai_analiz tablosu olusturuldu.';
END
ELSE
    PRINT 'uretim.banyo_tds_ai_analiz tablosu zaten mevcut.';
GO

-- 5. PERFORMANS INDEXLERI
-- banyo_analiz_sonuclari icin tarih bazli index (trend analizi performansi)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_banyo_analiz_banyo_tarih' AND object_id=OBJECT_ID('uretim.banyo_analiz_sonuclari'))
BEGIN
    CREATE INDEX IX_banyo_analiz_banyo_tarih ON uretim.banyo_analiz_sonuclari (banyo_id, tarih DESC);
    PRINT 'IX_banyo_analiz_banyo_tarih indexi olusturuldu.';
END
GO

-- TDS tablosunda banyo_id indexi
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_banyo_tds_banyo' AND object_id=OBJECT_ID('uretim.banyo_tds'))
BEGIN
    CREATE INDEX IX_banyo_tds_banyo ON uretim.banyo_tds (banyo_id, aktif_mi);
    PRINT 'IX_banyo_tds_banyo indexi olusturuldu.';
END
GO

-- AI analiz cache indexi
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name='IX_tds_ai_analiz_banyo' AND object_id=OBJECT_ID('uretim.banyo_tds_ai_analiz'))
BEGIN
    CREATE INDEX IX_tds_ai_analiz_banyo ON uretim.banyo_tds_ai_analiz (banyo_id, analiz_tarihi DESC);
    PRINT 'IX_tds_ai_analiz_banyo indexi olusturuldu.';
END
GO

PRINT '=== TDS Migration tamamlandi ===';
