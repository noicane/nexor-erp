-- =============================================
-- NEXOR ERP - Departman & Pozisyon Hiyerarşi Düzenlemesi
-- Tarih: 2026-03-31
-- =============================================
-- NOT: Bu script mevcut verileri kontrol eder, eksikleri ekler.
--      Önce SELECT ile mevcut durumu görün, sonra INSERT/UPDATE'leri çalıştırın.

USE AtmoLogicERP;
GO

-- =============================================
-- 1. MEVCUT DURUM KONTROLÜ
-- =============================================
PRINT '=== MEVCUT DEPARTMANLAR ==='
SELECT d.id, d.kod, d.ad, ust.ad AS ust_departman, d.aktif_mi
FROM ik.departmanlar d
LEFT JOIN ik.departmanlar ust ON d.ust_departman_id = ust.id
ORDER BY ISNULL(d.ust_departman_id, 0), d.kod;

PRINT '=== MEVCUT POZİSYONLAR ==='
SELECT p.id, p.kod, p.ad, d.ad AS departman, p.aktif_mi
FROM ik.pozisyonlar p
LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
ORDER BY d.ad, p.kod;

-- =============================================
-- 2. ANA DEPARTMANLAR (Üst seviye)
-- =============================================
-- Yoksa ekle, varsa dokunma

IF NOT EXISTS (SELECT 1 FROM ik.departmanlar WHERE kod = 'URETIM')
    INSERT INTO ik.departmanlar (kod, ad, aktif_mi) VALUES ('URETIM', 'Üretim', 1);

IF NOT EXISTS (SELECT 1 FROM ik.departmanlar WHERE kod = 'KALITE')
    INSERT INTO ik.departmanlar (kod, ad, aktif_mi) VALUES ('KALITE', 'Kalite', 1);

IF NOT EXISTS (SELECT 1 FROM ik.departmanlar WHERE kod = 'BAKIM')
    INSERT INTO ik.departmanlar (kod, ad, aktif_mi) VALUES ('BAKIM', 'Bakım', 1);

IF NOT EXISTS (SELECT 1 FROM ik.departmanlar WHERE kod = 'DESTEK')
    INSERT INTO ik.departmanlar (kod, ad, aktif_mi) VALUES ('DESTEK', 'Destek', 1);

IF NOT EXISTS (SELECT 1 FROM ik.departmanlar WHERE kod = 'SEVKIYAT')
    INSERT INTO ik.departmanlar (kod, ad, aktif_mi) VALUES ('SEVKIYAT', 'Sevkiyat', 1);

IF NOT EXISTS (SELECT 1 FROM ik.departmanlar WHERE kod = 'IK')
    INSERT INTO ik.departmanlar (kod, ad, aktif_mi) VALUES ('IK', 'İnsan Kaynakları', 1);

IF NOT EXISTS (SELECT 1 FROM ik.departmanlar WHERE kod = 'YONETIM')
    INSERT INTO ik.departmanlar (kod, ad, aktif_mi) VALUES ('YONETIM', 'Yönetim', 1);

-- =============================================
-- 3. ALT DEPARTMANLAR (Üretim altı)
-- =============================================

-- Üretim alt departmanları
DECLARE @uretim_id BIGINT = (SELECT id FROM ik.departmanlar WHERE kod = 'URETIM');

IF NOT EXISTS (SELECT 1 FROM ik.departmanlar WHERE kod = 'KTL')
    INSERT INTO ik.departmanlar (kod, ad, ust_departman_id, aktif_mi) VALUES ('KTL', 'Kataforez', @uretim_id, 1);
ELSE
    UPDATE ik.departmanlar SET ust_departman_id = @uretim_id WHERE kod = 'KTL' AND ust_departman_id IS NULL;

IF NOT EXISTS (SELECT 1 FROM ik.departmanlar WHERE kod = 'ZNNI')
    INSERT INTO ik.departmanlar (kod, ad, ust_departman_id, aktif_mi) VALUES ('ZNNI', 'Çinko-Nikel', @uretim_id, 1);
ELSE
    UPDATE ik.departmanlar SET ust_departman_id = @uretim_id WHERE kod = 'ZNNI' AND ust_departman_id IS NULL;

IF NOT EXISTS (SELECT 1 FROM ik.departmanlar WHERE kod = 'ON')
    INSERT INTO ik.departmanlar (kod, ad, ust_departman_id, aktif_mi) VALUES ('ON', 'Ön İşlem', @uretim_id, 1);
ELSE
    UPDATE ik.departmanlar SET ust_departman_id = @uretim_id WHERE kod = 'ON' AND ust_departman_id IS NULL;

-- =============================================
-- 4. POZİSYONLAR (Bölümler)
-- =============================================

-- Kataforez altı pozisyonlar
DECLARE @ktl_id BIGINT = (SELECT id FROM ik.departmanlar WHERE kod = 'KTL');

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'ASKILAMA')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('ASKILAMA', 'Askılama', @ktl_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'ASKILAMA_TOPLAMA')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('ASKILAMA_TOPLAMA', 'Askılama-Toplama', @ktl_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'CINKO_ASKILAMA')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('CINKO_ASKILAMA', 'Çinko Askılama', @ktl_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'KTL_FINAL_KALITE')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('KTL_FINAL_KALITE', 'KTL Final Kalite Kontrol', @ktl_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'KTL_OPERATOR')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('KTL_OPERATOR', 'Kataforez Operatör', @ktl_id, 1);

-- Çinko-Nikel altı pozisyonlar
DECLARE @znni_id BIGINT = (SELECT id FROM ik.departmanlar WHERE kod = 'ZNNI');

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'ZNNI_OPERATOR')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('ZNNI_OPERATOR', 'Çinko-Nikel Operatör', @znni_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'ZNNI_ASKILAMA')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('ZNNI_ASKILAMA', 'Çinko-Nikel Askılama', @znni_id, 1);

-- Ön İşlem altı pozisyonlar
DECLARE @on_id BIGINT = (SELECT id FROM ik.departmanlar WHERE kod = 'ON');

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'ON_OPERATOR')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('ON_OPERATOR', 'Ön İşlem Operatör', @on_id, 1);

-- Bakım pozisyonları
DECLARE @bakim_id BIGINT = (SELECT id FROM ik.departmanlar WHERE kod = 'BAKIM');

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'ELEKTRONIK_BAKIM')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('ELEKTRONIK_BAKIM', 'Elektronik Bakım', @bakim_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'MEKANIK_BAKIM')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('MEKANIK_BAKIM', 'Mekanik Bakım', @bakim_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'KAYNAK_USTASI')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('KAYNAK_USTASI', 'Kaynak Ustası', @bakim_id, 1);

-- Destek pozisyonları
DECLARE @destek_id BIGINT = (SELECT id FROM ik.departmanlar WHERE kod = 'DESTEK');

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'GENEL')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('GENEL', 'Genel', @destek_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'SEVKIYAT_PER')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('SEVKIYAT_PER', 'Sevkiyat', @destek_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'URETIM_DESTEK_SARILMA')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('URETIM_DESTEK_SARILMA', 'Üretim Destek Sarılma', @destek_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'URETIM_DESTEK_SOKUM')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('URETIM_DESTEK_SOKUM', 'Üretim Destek Söküm', @destek_id, 1);

-- Kalite pozisyonları
DECLARE @kalite_id BIGINT = (SELECT id FROM ik.departmanlar WHERE kod = 'KALITE');

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'KALITE_KONTROL')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('KALITE_KONTROL', 'Kalite Kontrol', @kalite_id, 1);

IF NOT EXISTS (SELECT 1 FROM ik.pozisyonlar WHERE kod = 'FINAL_KALITE')
    INSERT INTO ik.pozisyonlar (kod, ad, departman_id, aktif_mi) VALUES ('FINAL_KALITE', 'Final Kalite Kontrol', @kalite_id, 1);

-- =============================================
-- 5. SONUÇ KONTROLÜ
-- =============================================
PRINT '=== GÜNCEL DEPARTMAN HİYERARŞİSİ ==='
SELECT
    d.id, d.kod, d.ad,
    ISNULL(ust.ad, '(Ana)') AS ust_departman,
    d.aktif_mi,
    (SELECT COUNT(*) FROM ik.pozisyonlar WHERE departman_id = d.id AND aktif_mi = 1) AS pozisyon_sayisi,
    (SELECT COUNT(*) FROM ik.personeller WHERE departman_id = d.id AND aktif_mi = 1) AS personel_sayisi
FROM ik.departmanlar d
LEFT JOIN ik.departmanlar ust ON d.ust_departman_id = ust.id
WHERE d.aktif_mi = 1
ORDER BY ISNULL(ust.kod, d.kod), d.kod;

PRINT '=== GÜNCEL POZİSYONLAR ==='
SELECT
    p.id, p.kod, p.ad, d.ad AS departman,
    ust.ad AS ust_departman,
    p.aktif_mi,
    (SELECT COUNT(*) FROM ik.personeller WHERE pozisyon_id = p.id AND aktif_mi = 1) AS personel_sayisi
FROM ik.pozisyonlar p
LEFT JOIN ik.departmanlar d ON p.departman_id = d.id
LEFT JOIN ik.departmanlar ust ON d.ust_departman_id = ust.id
WHERE p.aktif_mi = 1
ORDER BY ISNULL(ust.kod, d.kod), d.kod, p.kod;
GO
