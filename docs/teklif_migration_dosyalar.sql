-- ============================================
-- NEXOR ERP - Teklif Modulu Dosya Alanlari Migration
-- Tarih: 2026-02-16
-- Aciklama: Kaplama sartnamesi ve parca gorseli icin yeni sutunlar
-- ============================================

-- Kaplama sartnamesi dosya yolu
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID(N'satislar.teklifler') AND name = 'kaplama_sartnamesi_dosya'
)
BEGIN
    ALTER TABLE satislar.teklifler
    ADD kaplama_sartnamesi_dosya NVARCHAR(500) NULL;
    PRINT 'kaplama_sartnamesi_dosya sutunu eklendi.';
END
GO

-- Parca gorseli dosya yolu
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID(N'satislar.teklifler') AND name = 'parca_gorseli_dosya'
)
BEGIN
    ALTER TABLE satislar.teklifler
    ADD parca_gorseli_dosya NVARCHAR(500) NULL;
    PRINT 'parca_gorseli_dosya sutunu eklendi.';
END
GO

-- Yillik adet (dahili bilgi - PDF'de gorunmez)
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID(N'satislar.teklifler') AND name = 'yillik_adet'
)
BEGIN
    ALTER TABLE satislar.teklifler
    ADD yillik_adet INT NULL;
    PRINT 'yillik_adet sutunu eklendi.';
END
GO

-- Yillik ciro (dahili bilgi - PDF'de gorunmez)
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID(N'satislar.teklifler') AND name = 'yillik_ciro'
)
BEGIN
    ALTER TABLE satislar.teklifler
    ADD yillik_ciro DECIMAL(18,2) NULL;
    PRINT 'yillik_ciro sutunu eklendi.';
END
GO

-- Dahili not (PDF'de gorunmez)
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID(N'satislar.teklifler') AND name = 'dahili_not'
)
BEGIN
    ALTER TABLE satislar.teklifler
    ADD dahili_not NVARCHAR(MAX) NULL;
    PRINT 'dahili_not sutunu eklendi.';
END
GO

-- Satir gorseli dosya yolu (teklif_satirlari tablosunda)
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID(N'satislar.teklif_satirlari') AND name = 'gorsel_dosya'
)
BEGIN
    ALTER TABLE satislar.teklif_satirlari
    ADD gorsel_dosya NVARCHAR(500) NULL;
    PRINT 'teklif_satirlari.gorsel_dosya sutunu eklendi.';
END
GO

-- Yillik adet (satir bazli - PDF'de gorunmez)
IF NOT EXISTS (
    SELECT * FROM sys.columns
    WHERE object_id = OBJECT_ID(N'satislar.teklif_satirlari') AND name = 'yillik_adet'
)
BEGIN
    ALTER TABLE satislar.teklif_satirlari
    ADD yillik_adet INT NULL;
    PRINT 'teklif_satirlari.yillik_adet sutunu eklendi.';
END
GO

PRINT 'Teklif migration tamamlandi.';
GO
