-- =============================================
-- NEXOR ERP Migration 0003 - Modul Lisans Sistemi
-- =============================================
-- ONEMLI: AtmoLogicERP'de zaten 'sistem.moduller' tablosu var (RBAC yetki sistemi).
-- Dokunulmaz. Lisans sistemi icin AYRI schema ('lisans') kullanilir.
--
-- lisans.moduller:       ana modullerin tanimlari (20 modul)
-- lisans.modul_durumlari: musteri bazli aktivasyon (aktif + bitis tarihi + notlar)
--
-- Seed: 20 ana modul (tumu aktif=1, dashboard+sistem+tanimlar zorunlu=1)
-- Atmo davranisi degismez - hepsi aktif baslar.
-- =============================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'lisans')
    EXEC('CREATE SCHEMA lisans');
GO

-- 1) lisans.moduller (tanim)
IF NOT EXISTS (
    SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'lisans' AND t.name = 'moduller'
)
BEGIN
    CREATE TABLE lisans.moduller (
        modul_kodu   NVARCHAR(50)  COLLATE DATABASE_DEFAULT NOT NULL PRIMARY KEY,
        modul_adi    NVARCHAR(200) NOT NULL,
        kategori     NVARCHAR(50)  NULL,
        ikon         NVARCHAR(50)  NULL,
        sira         INT           NOT NULL DEFAULT 100,
        zorunlu      BIT           NOT NULL DEFAULT 0,
        aciklama     NVARCHAR(500) NULL
    );
    PRINT 'lisans.moduller tablosu olusturuldu';
END
ELSE
    PRINT 'lisans.moduller zaten mevcut';
GO

-- 2) lisans.modul_durumlari (aktivasyon)
IF NOT EXISTS (
    SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'lisans' AND t.name = 'modul_durumlari'
)
BEGIN
    CREATE TABLE lisans.modul_durumlari (
        modul_kodu        NVARCHAR(50)  COLLATE DATABASE_DEFAULT NOT NULL PRIMARY KEY,
        aktif             BIT           NOT NULL DEFAULT 1,
        bitis_tarihi      DATETIME2     NULL,
        aktivasyon_tarihi DATETIME2     NOT NULL DEFAULT (GETDATE()),
        notlar            NVARCHAR(500) NULL,
        CONSTRAINT FK_modul_durumlari_modul FOREIGN KEY (modul_kodu)
            REFERENCES lisans.moduller(modul_kodu)
    );
    PRINT 'lisans.modul_durumlari tablosu olusturuldu';
END
ELSE
    PRINT 'lisans.modul_durumlari zaten mevcut';
GO

-- 3) Seed moduller (MERGE: idempotent)
MERGE lisans.moduller AS dst
USING (VALUES
    ('dashboard',   N'Dashboard',               N'Genel',      'dashboard',    10,  1),
    ('cariler',     N'Cariler',                 N'Ticari',     'users',        20,  0),
    ('stok',        N'Stok Kartlari',           N'Stok',       'box',          30,  0),
    ('teklifler',   N'Teklifler',               N'Ticari',     'document',     40,  0),
    ('is_emirleri', N'Is Emirleri',             N'Uretim',     'clipboard',    50,  0),
    ('uretim',      N'Uretim',                  N'Uretim',     'factory',      60,  0),
    ('kalite',      N'Kalite',                  N'Kalite',     'check',        70,  0),
    ('laboratuvar', N'Laboratuvar',             N'Kalite',     'flask',        80,  0),
    ('sevkiyat',    N'Sevkiyat',                N'Lojistik',   'truck',        90,  0),
    ('satinalma',   N'Satinalma',               N'Ticari',     'cart',        100,  0),
    ('depo',        N'Depo / Emanet',           N'Lojistik',   'warehouse',   110,  0),
    ('ik',          N'Insan Kaynaklari',        N'IK',         'user-badge',  120,  0),
    ('bakim',       N'Bakim',                   N'Bakim',      'wrench',      130,  0),
    ('isg',         N'Is Sagligi Guvenligi',    N'ISG',        'shield',      140,  0),
    ('cevre',       N'Cevre Yonetimi',          N'Cevre',      'leaf',        150,  0),
    ('aksiyonlar',  N'Aksiyonlar',              N'Genel',      'list',        160,  0),
    ('raporlar',    N'Raporlar',                N'Analiz',     'chart',       170,  0),
    ('tanimlar',    N'Tanimlar',                N'Sistem',     'gear',        180,  1),
    ('yonetim',     N'Yonetim',                 N'Yonetim',    'crown',       190,  0),
    ('sistem',      N'Sistem',                  N'Sistem',     'lock',        200,  1)
) AS src (modul_kodu, modul_adi, kategori, ikon, sira, zorunlu)
ON dst.modul_kodu = src.modul_kodu
WHEN NOT MATCHED BY TARGET THEN
    INSERT (modul_kodu, modul_adi, kategori, ikon, sira, zorunlu)
    VALUES (src.modul_kodu, src.modul_adi, src.kategori, src.ikon, src.sira, src.zorunlu);
GO

PRINT 'lisans.moduller seed tamamlandi';
GO

-- 4) Seed durumlar (hepsi aktif=1)
INSERT INTO lisans.modul_durumlari (modul_kodu, aktif, notlar)
SELECT m.modul_kodu, 1, N'Ilk kurulum - tum moduller aktif'
FROM lisans.moduller m
WHERE NOT EXISTS (
    SELECT 1 FROM lisans.modul_durumlari d WHERE d.modul_kodu = m.modul_kodu
);
GO

PRINT 'lisans.modul_durumlari seed tamamlandi';
GO
