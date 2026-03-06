-- Banyo Tanımları - Serbest Asit Parametreleri Ekleme
-- Tarih: 2026-02-18

-- Serbest Asit kolonlarını ekle (eğer yoksa)
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('uretim.banyo_tanimlari') AND name = 'serbest_asit_min')
BEGIN
    ALTER TABLE uretim.banyo_tanimlari ADD serbest_asit_min DECIMAL(10,4) NULL;
    ALTER TABLE uretim.banyo_tanimlari ADD serbest_asit_max DECIMAL(10,4) NULL;
    ALTER TABLE uretim.banyo_tanimlari ADD serbest_asit_hedef DECIMAL(10,4) NULL;
    PRINT 'Serbest asit kolonlari eklendi.';
END
ELSE
    PRINT 'Serbest asit kolonlari zaten mevcut.';
