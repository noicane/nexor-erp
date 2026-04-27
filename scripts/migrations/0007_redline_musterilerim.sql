-- =============================================
-- NEXOR ERP Migration 0007 - Bayi Master: redline.musterilerim
-- =============================================
-- Bayinin (Redline) merkezi musteri tablosu. NEXOR'un her musteri kurulumunda
-- yerel config.json'da yasayan profil bilgileri, bayi tarafinda ayrica burada
-- toplu/kucuk ozet halinde takip edilir.
--
-- KULLANIM: Bayi panelindeki Musteri Yonetimi ekraninda her kayit Kaydet'te
-- redline_master_sync.push_musteri() ile bu tabloya UPSERT edilir.
--
-- Bu tablo, "ATLAS_KATAFOREZ_..." veya benzeri musteri DB'sinde DEGIL,
-- bayinin merkezi yonetim DB'sinde (REDLINE_MASTER) tutulmali. Kurulum
-- icin ayrica bir baglanti string'i gerekecek (ileride yapilacak).
-- =============================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'redline')
    EXEC('CREATE SCHEMA redline');
GO

-- 1) redline.musterilerim - bayi master musteri ozeti
IF NOT EXISTS (
    SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'redline' AND t.name = 'musterilerim'
)
BEGIN
    CREATE TABLE redline.musterilerim (
        id                 INT IDENTITY(1,1) PRIMARY KEY,
        musteri_kodu       NVARCHAR(60)  COLLATE DATABASE_DEFAULT NOT NULL UNIQUE,
        musteri_adi        NVARCHAR(200) NOT NULL,
        kisa_ad            NVARCHAR(60)  NULL,
        musteri_tipi       NVARCHAR(20)  NULL,    -- DEMO/AKTIF/ESKI/PILOT
        durum              NVARCHAR(20)  NULL,    -- AKTIF/PASIF/ASKIDA
        segment            NVARCHAR(40)  NULL,
        sektor             NVARCHAR(80)  NULL,
        sorumlu_personel   NVARCHAR(80)  NULL,

        vkn_tckn           NVARCHAR(20)  NULL,
        telefon            NVARCHAR(40)  NULL,
        email              NVARCHAR(120) NULL,
        web                NVARCHAR(120) NULL,

        -- Anlasma
        sozlesme_no        NVARCHAR(50)  NULL,
        anlasma_baslangic  DATE          NULL,
        anlasma_bitis      DATE          NULL,
        lisans_tipi        NVARCHAR(20)  NULL,
        bedel              DECIMAL(15,2) NULL,
        para_birimi        NVARCHAR(10)  NULL,
        kullanici_limiti   INT           NULL,

        -- Bakim
        bakim_var          BIT           NOT NULL DEFAULT 0,
        bakim_aylik_ucret  DECIMAL(15,2) NULL,
        bakim_bitis        DATE          NULL,

        -- Kurulum
        kurulum_tipi       NVARCHAR(20)  NULL,    -- ON_PREM/CLOUD
        nexor_versiyonu    NVARCHAR(40)  NULL,
        sql_surumu         NVARCHAR(80)  NULL,
        son_guncelleme     DATE          NULL,

        -- Finansal
        zirve_cari_kodu    NVARCHAR(40)  NULL,
        cari_bakiye        DECIMAL(15,2) NULL,
        kredi_limiti       DECIMAL(15,2) NULL,
        risk_skoru         NVARCHAR(20)  NULL,

        -- Tam profil JSON snapshot'i (raw)
        profil_json        NVARCHAR(MAX) NULL,

        -- Audit
        olusturma_tarihi   DATETIME2     NOT NULL DEFAULT SYSDATETIME(),
        son_sync_tarihi    DATETIME2     NOT NULL DEFAULT SYSDATETIME(),
        son_sync_pc        NVARCHAR(120) NULL,
        son_sync_kullanici NVARCHAR(80)  NULL
    );

    -- Sik aranan alanlar
    CREATE INDEX IX_redline_musterilerim_durum
        ON redline.musterilerim (durum);
    CREATE INDEX IX_redline_musterilerim_anlasma_bitis
        ON redline.musterilerim (anlasma_bitis);
    CREATE INDEX IX_redline_musterilerim_bakim_bitis
        ON redline.musterilerim (bakim_bitis) WHERE bakim_var = 1;

    PRINT 'redline.musterilerim tablosu olusturuldu';
END
ELSE
    PRINT 'redline.musterilerim zaten mevcut';
GO

-- 2) Sync log: sync hatalari ve gecmisi
IF NOT EXISTS (
    SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'redline' AND t.name = 'sync_log'
)
BEGIN
    CREATE TABLE redline.sync_log (
        id              INT IDENTITY(1,1) PRIMARY KEY,
        zaman           DATETIME2    NOT NULL DEFAULT SYSDATETIME(),
        musteri_kodu    NVARCHAR(60) NULL,
        islem           NVARCHAR(40) NOT NULL,   -- PUSH/PULL/UPSERT/DELETE
        sonuc           NVARCHAR(20) NOT NULL,   -- BASARILI/HATA
        mesaj           NVARCHAR(MAX) NULL,
        kaynak_pc       NVARCHAR(120) NULL
    );
    PRINT 'redline.sync_log tablosu olusturuldu';
END
ELSE
    PRINT 'redline.sync_log zaten mevcut';
GO
