-- Geri-doldurma: kalite.final_kontrol'de hatali_adet > 0 olan eski kayıtlar için
-- kalite.uretim_redler'e eksik satırları ekler.
-- Bug: parçalı kontrollerde INSERT atlanıyordu (kalite_final_kontrol.py:1921-1944 eski hali).
-- Düzeltildi, ama tarihsel kayıplar bu scriptle kapatılır.
--
-- Çalıştırma önce PREVIEW, sonra INSERT:
--   1) Önce alttaki SELECT ile kaç kayıt eklenecek kontrol et.
--   2) Sonuç doğruysa INSERT bloğunu tek çalıştır.

USE AtmoLogicERP;
GO

-- ========= PREVIEW: Eklenecek kayıtlar =========
SELECT
    fk.id                AS kontrol_id,
    fk.is_emri_id,
    fk.lot_no,
    fk.hatali_adet       AS red_miktar,
    fk.kontrol_eden_id,
    fk.kontrol_tarihi,
    fk.aciklama
FROM kalite.final_kontrol fk
WHERE fk.hatali_adet > 0
  AND NOT EXISTS (
        SELECT 1
        FROM kalite.uretim_redler ur
        WHERE ur.kontrol_id = fk.id
  )
ORDER BY fk.kontrol_tarihi DESC;
GO

-- ========= BACKFILL: Eksik red kayıtlarını ekle =========
-- Yukarıdaki SELECT sonucu doğruysa aşağıyı çalıştır.

BEGIN TRANSACTION;

INSERT INTO kalite.uretim_redler
    (is_emri_id, lot_no, red_miktar, kontrol_id, red_tarihi,
     kontrol_eden_id, durum, aciklama, olusturma_tarihi)
SELECT
    fk.is_emri_id,
    fk.lot_no,
    fk.hatali_adet,
    fk.id,
    fk.kontrol_tarihi,
    fk.kontrol_eden_id,
    'BEKLIYOR',
    ISNULL(fk.aciklama, N'Geri-doldurma (parcali kontrol bug fix)'),
    fk.olusturma_tarihi
FROM kalite.final_kontrol fk
WHERE fk.hatali_adet > 0
  AND NOT EXISTS (
        SELECT 1
        FROM kalite.uretim_redler ur
        WHERE ur.kontrol_id = fk.id
  );

-- Eklenen kayıt sayısını göster
SELECT @@ROWCOUNT AS eklenen_kayit_sayisi;

-- Tamam ise:
COMMIT TRANSACTION;
-- Sorun varsa:
-- ROLLBACK TRANSACTION;
GO

-- ========= DOĞRULAMA =========
SELECT
    'final_kontrol (hatali_adet>0)' AS kaynak,
    COUNT(*) AS adet
FROM kalite.final_kontrol WHERE hatali_adet > 0
UNION ALL
SELECT
    'uretim_redler (toplam)',
    COUNT(*)
FROM kalite.uretim_redler;
GO
