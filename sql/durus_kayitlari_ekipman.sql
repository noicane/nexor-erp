-- Duruş Kayıtları: ekipman_id kolonu ekleme
-- uretim.durus_kayitlari tablosuna ekipman referansı

IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('uretim.durus_kayitlari')
    AND name = 'ekipman_id'
)
BEGIN
    ALTER TABLE uretim.durus_kayitlari
    ADD ekipman_id BIGINT NULL;
END
GO

-- Durum kolonu (ACIK, BAKIMDA, KAPALI)
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('uretim.durus_kayitlari')
    AND name = 'durum'
)
BEGIN
    ALTER TABLE uretim.durus_kayitlari
    ADD durum NVARCHAR(20) NOT NULL DEFAULT 'ACIK';
END
GO

-- Kapatan bakımcı
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('uretim.durus_kayitlari')
    AND name = 'kapatan_id'
)
BEGIN
    ALTER TABLE uretim.durus_kayitlari
    ADD kapatan_id BIGINT NULL;
END
GO

-- Kapatma notu
IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('uretim.durus_kayitlari')
    AND name = 'kapatma_notu'
)
BEGIN
    ALTER TABLE uretim.durus_kayitlari
    ADD kapatma_notu NVARCHAR(1000) NULL;
END
GO
