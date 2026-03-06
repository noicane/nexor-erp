-- ============================================================================
-- NEXOR ERP - Aksiyon Ekleri (Dosya/Resim) Migration
-- Tarih: 2026-02-18
-- Aciklama: Aksiyonlara dosya/resim ekleme altyapisi
-- ============================================================================

USE AtmoLogicERP;
GO

PRINT '=== NEXOR Aksiyon Ekler Migration Basliyor ===';
GO

-- ============================================================================
-- 1. sistem.aksiyon_ekler - Dosya/resim ekleri tablosu
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE schema_id = SCHEMA_ID('sistem') AND name = 'aksiyon_ekler')
BEGIN
    CREATE TABLE sistem.aksiyon_ekler (
        id                  BIGINT IDENTITY(1,1) PRIMARY KEY,
        aksiyon_id          BIGINT NOT NULL,
        dosya_adi           NVARCHAR(300) NOT NULL,         -- Orijinal dosya adi
        dosya_yolu          NVARCHAR(1000) NOT NULL,        -- UNC path (\\AtlasNAS\...)
        dosya_boyutu        BIGINT NULL,                    -- Byte cinsinden
        dosya_tipi          NVARCHAR(50) NULL,              -- Uzanti (.pdf, .jpg, .xlsx vb.)
        aciklama            NVARCHAR(500) NULL,
        yukleyen_id         BIGINT NOT NULL,
        olusturma_tarihi    DATETIME2 NOT NULL DEFAULT(GETDATE()),
        silindi_mi          BIT NOT NULL DEFAULT(0),
        silen_id            BIGINT NULL,
        silinme_tarihi      DATETIME2 NULL,

        CONSTRAINT FK_aksiyon_ekler_aksiyon
            FOREIGN KEY (aksiyon_id) REFERENCES sistem.aksiyonlar(id),
        CONSTRAINT FK_aksiyon_ekler_yukleyen
            FOREIGN KEY (yukleyen_id) REFERENCES sistem.kullanicilar(id)
    );

    CREATE NONCLUSTERED INDEX IX_aksiyon_ekler_aksiyon
    ON sistem.aksiyon_ekler (aksiyon_id, silindi_mi)
    INCLUDE (dosya_adi, dosya_tipi, dosya_boyutu, olusturma_tarihi);

    PRINT '  [+] sistem.aksiyon_ekler tablosu olusturuldu';
END
GO


-- ============================================================================
-- 2. vw_aksiyon_ozet - ek_sayisi kolonu ekle (view'u yeniden olustur)
-- ============================================================================

IF OBJECT_ID('sistem.vw_aksiyon_ozet', 'V') IS NOT NULL
    DROP VIEW sistem.vw_aksiyon_ozet;
GO

CREATE VIEW sistem.vw_aksiyon_ozet
AS
SELECT
    a.id,
    a.aksiyon_no,
    a.baslik,
    a.aciklama,
    a.kategori,
    a.kaynak_modul,
    a.oncelik,
    a.durum,
    a.hedef_tarih,
    a.tamamlanma_orani,
    a.tamamlanma_tarihi,
    a.olusturma_tarihi,
    a.sorumlu_id,
    p.ad + ' ' + p.soyad AS sorumlu_adi,
    d.ad AS departman_adi,
    a.sorumlu_departman_id,
    a.talep_eden_id,
    tp.ad + ' ' + tp.soyad AS talep_eden_adi,
    CASE
        WHEN a.durum = 'TAMAMLANDI' OR a.durum = 'DOGRULANDI' THEN 0
        WHEN a.hedef_tarih IS NULL THEN 0
        WHEN a.hedef_tarih < CAST(GETDATE() AS DATE) THEN
            DATEDIFF(DAY, a.hedef_tarih, CAST(GETDATE() AS DATE))
        ELSE 0
    END AS gecikme_gun,
    CASE
        WHEN a.hedef_tarih IS NULL THEN NULL
        WHEN a.durum IN ('TAMAMLANDI', 'DOGRULANDI', 'IPTAL') THEN NULL
        ELSE DATEDIFF(DAY, CAST(GETDATE() AS DATE), a.hedef_tarih)
    END AS kalan_gun,
    (SELECT COUNT(*) FROM sistem.aksiyon_yorumlar y WHERE y.aksiyon_id = a.id) AS yorum_sayisi,
    (SELECT COUNT(*) FROM sistem.aksiyon_ekler e WHERE e.aksiyon_id = a.id AND e.silindi_mi = 0) AS ek_sayisi
FROM sistem.aksiyonlar a
LEFT JOIN ik.personeller p ON p.id = a.sorumlu_id
LEFT JOIN ik.departmanlar d ON d.id = a.sorumlu_departman_id
LEFT JOIN ik.personeller tp ON tp.id = a.talep_eden_id
WHERE a.silindi_mi = 0 AND a.aktif_mi = 1;
GO

PRINT '  [+] sistem.vw_aksiyon_ozet view guncellendi (ek_sayisi eklendi)';
GO


-- ============================================================================
-- TAMAMLANDI
-- ============================================================================

PRINT '';
PRINT '=== NEXOR Aksiyon Ekler Migration TAMAMLANDI ===';
PRINT '';
PRINT 'Olusturulan/guncellenen nesneler:';
PRINT '  Tablolar:';
PRINT '    - sistem.aksiyon_ekler (yeni tablo)';
PRINT '  Viewler:';
PRINT '    - sistem.vw_aksiyon_ozet (guncellendi: +ek_sayisi, +aciklama)';
GO
