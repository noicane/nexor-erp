-- NEXOR ERP - Kimyasal Tuketim Takip Tablolari
-- B Yaklasimi: TDS bazli tuketim hesaplama

-- 1. Banyo Kimyasal TDS Formulleri
-- Her banyo icin hangi kimyasal ne oranda tuketilir
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'banyo_kimyasal_tds' AND schema_id = SCHEMA_ID('uretim'))
CREATE TABLE uretim.banyo_kimyasal_tds (
    id BIGINT IDENTITY(1,1) NOT NULL,
    uuid UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    banyo_id BIGINT NOT NULL,
    kimyasal_id BIGINT NOT NULL,
    tuketim_orani DECIMAL(12,6) NOT NULL,
    tuketim_birimi NVARCHAR(20) NOT NULL,
    hedef_konsantrasyon DECIMAL(10,4) NULL,
    konsantrasyon_birimi NVARCHAR(20) NULL,
    kritik_seviye DECIMAL(10,4) NULL,
    aktif_mi BIT NOT NULL DEFAULT 1,
    notlar NVARCHAR(500) NULL,
    olusturma_tarihi DATETIME2 NOT NULL DEFAULT GETDATE(),
    guncelleme_tarihi DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT PK_banyo_kimyasal_tds PRIMARY KEY (id),
    CONSTRAINT FK_bkt_banyo FOREIGN KEY (banyo_id) REFERENCES uretim.banyo_tanimlari(id),
    CONSTRAINT FK_bkt_kimyasal FOREIGN KEY (kimyasal_id) REFERENCES stok.urunler(id),
    CONSTRAINT UQ_bkt_banyo_kimyasal UNIQUE (banyo_id, kimyasal_id)
);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_bkt_banyo')
CREATE INDEX IX_bkt_banyo ON uretim.banyo_kimyasal_tds(banyo_id);
GO
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_bkt_kimyasal')
CREATE INDEX IX_bkt_kimyasal ON uretim.banyo_kimyasal_tds(kimyasal_id);
GO

-- 2. Kimyasal Tuketim Kayitlari
-- Gercek tuketim + tahmini tuketim kayitlari
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'kimyasal_tuketim' AND schema_id = SCHEMA_ID('uretim'))
CREATE TABLE uretim.kimyasal_tuketim (
    id BIGINT IDENTITY(1,1) NOT NULL,
    uuid UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID(),
    banyo_id BIGINT NOT NULL,
    kimyasal_id BIGINT NOT NULL,
    tarih DATETIME2 NOT NULL DEFAULT GETDATE(),
    islem_tipi NVARCHAR(20) NOT NULL,
    miktar DECIMAL(12,4) NOT NULL,
    birim NVARCHAR(20) NOT NULL DEFAULT 'KG',
    neden NVARCHAR(100) NULL,
    yapan_id BIGINT NULL,
    stok_hareket_id BIGINT NULL,
    tahmini_miktar DECIMAL(12,4) NULL,
    lot_no NVARCHAR(50) NULL,
    notlar NVARCHAR(500) NULL,
    olusturma_tarihi DATETIME2 NOT NULL DEFAULT GETDATE(),
    CONSTRAINT PK_kimyasal_tuketim PRIMARY KEY (id),
    CONSTRAINT FK_kt_banyo FOREIGN KEY (banyo_id) REFERENCES uretim.banyo_tanimlari(id),
    CONSTRAINT FK_kt_kimyasal FOREIGN KEY (kimyasal_id) REFERENCES stok.urunler(id)
);
GO

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_kt_banyo_tarih')
CREATE INDEX IX_kt_banyo_tarih ON uretim.kimyasal_tuketim(banyo_id, tarih);
GO
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_kt_kimyasal')
CREATE INDEX IX_kt_kimyasal ON uretim.kimyasal_tuketim(kimyasal_id);
GO
