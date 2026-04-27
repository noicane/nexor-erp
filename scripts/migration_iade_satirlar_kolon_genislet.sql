-- =============================================
-- NEXOR ERP - Migration: iade_irsaliye_satirlar kolon genislet
-- Tarih: 2026-04-24
-- Sebep: stok.urunler.urun_adi NVARCHAR(250) iken iade_irsaliye_satirlar.stok_adi
--        NVARCHAR(200) idi. Uzun urun adlarinda "Dize kesilecek" (8152) hatasi.
-- =============================================

USE AtmoLogicERP;
GO

-- stok_adi: 200 -> 250 (kaynakla hizala)
IF EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('siparis.iade_irsaliye_satirlar')
      AND name = 'stok_adi'
      AND max_length = 400   -- NVARCHAR(200) = 400 byte
)
BEGIN
    ALTER TABLE siparis.iade_irsaliye_satirlar
        ALTER COLUMN stok_adi NVARCHAR(250) NULL;
    PRINT 'stok_adi NVARCHAR(250) olarak guncellendi';
END
ELSE
    PRINT 'stok_adi zaten 250 veya daha uzun';
GO

-- iade_nedeni: 200 -> 500 (kullanici serbest metin girebilir)
IF EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('siparis.iade_irsaliye_satirlar')
      AND name = 'iade_nedeni'
      AND max_length = 400   -- NVARCHAR(200) = 400 byte
)
BEGIN
    ALTER TABLE siparis.iade_irsaliye_satirlar
        ALTER COLUMN iade_nedeni NVARCHAR(500) NULL;
    PRINT 'iade_nedeni NVARCHAR(500) olarak guncellendi';
END
ELSE
    PRINT 'iade_nedeni zaten 500 veya daha uzun';
GO

PRINT 'Migration tamamlandi.';
GO
