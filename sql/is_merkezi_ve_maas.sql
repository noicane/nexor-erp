-- İş Merkezi Tanımları + Personel Maaş + Personel-İş Merkezi Atama
-- ================================================================

-- 1. İş Merkezi Tanımları (hiyerarşik)
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='is_merkezleri' AND schema_id=SCHEMA_ID('tanim'))
BEGIN
    CREATE TABLE tanim.is_merkezleri (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        kod NVARCHAR(30) NOT NULL,
        ad NVARCHAR(150) NOT NULL,
        ust_merkez_id BIGINT NULL REFERENCES tanim.is_merkezleri(id),
        hat_id BIGINT NULL,
        aciklama NVARCHAR(500) NULL,
        sira INT NULL DEFAULT 0,
        aktif_mi BIT NOT NULL DEFAULT 1,
        olusturma_tarihi DATETIME2 NOT NULL DEFAULT GETDATE()
    );
END
GO

-- 2. Personel Maaş Kolonları
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('ik.personeller') AND name = 'brut_maas'
)
BEGIN
    ALTER TABLE ik.personeller ADD brut_maas DECIMAL(18,2) NULL;
    ALTER TABLE ik.personeller ADD net_maas DECIMAL(18,2) NULL;
END
GO

-- 3. Personel-İş Merkezi Atama (ay bazında)
IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE name='personel_is_merkezi' AND schema_id=SCHEMA_ID('maliyet'))
BEGIN
    -- Schema yoksa oluştur
    IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name='maliyet')
        EXEC('CREATE SCHEMA maliyet');

    CREATE TABLE maliyet.personel_is_merkezi (
        id BIGINT IDENTITY(1,1) PRIMARY KEY,
        personel_id BIGINT NOT NULL,
        is_merkezi_id BIGINT NOT NULL REFERENCES tanim.is_merkezleri(id),
        yil INT NOT NULL,
        ay INT NOT NULL,
        oran DECIMAL(5,2) NOT NULL DEFAULT 100.00,
        olusturma_tarihi DATETIME2 NOT NULL DEFAULT GETDATE()
    );
END
GO
