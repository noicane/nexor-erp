-- =============================================
-- NEXOR ERP Migration 0004 - Musteri Urun Kod Eslestirme
-- =============================================
-- Problem: Musteri (cari) kendi stok kodu ile parca gonderiyor,
--          biz ise kendi urun kodumuzla izliyoruz.
--          Fuzzy match yetersiz (ornek: "20003728 Teleskopprofil XL Kaynakli"
--          vs "719003K KATAFOREZ KAPLAMA 524R" - hicbir benzerlik yok).
--
-- Cozum: Bir kere manuel eslestir, tabloya kaydet. Ikinci sefer otomatik.
--        Her basarili eslestirme "ogrenilmis" olur ve zamanla sistem
--        kendini ogretir.
-- =============================================

IF NOT EXISTS (
    SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'musteri' AND t.name = 'musteri_urun_kodlari'
)
BEGIN
    CREATE TABLE musteri.musteri_urun_kodlari (
        id                BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
        cari_id           BIGINT NOT NULL,
        musteri_stok_kodu NVARCHAR(50) COLLATE DATABASE_DEFAULT NOT NULL,
        musteri_stok_adi  NVARCHAR(250) NULL,   -- Bilgi amacli, ogrenmeye yardim
        urun_id           BIGINT NOT NULL,      -- Bizim stok.urunler.id
        kaplama_hint      NVARCHAR(50) NULL,    -- KTFRZ / ZNNI - cari bazli
        olusturan_id      BIGINT NULL,
        olusturma_tarihi  DATETIME2 NOT NULL DEFAULT (GETDATE()),
        son_kullanim      DATETIME2 NULL,
        kullanim_sayisi   INT NOT NULL DEFAULT 0,
        notlar            NVARCHAR(500) NULL,
        CONSTRAINT FK_musteri_urun_cari FOREIGN KEY (cari_id)
            REFERENCES musteri.cariler(id),
        CONSTRAINT FK_musteri_urun_urun FOREIGN KEY (urun_id)
            REFERENCES stok.urunler(id)
    );

    -- Ayni (cari, musteri_kodu) tekrarlanmasin - unique
    CREATE UNIQUE INDEX UX_musteri_urun_cari_kod
        ON musteri.musteri_urun_kodlari (cari_id, musteri_stok_kodu);

    -- Lookup performansi
    CREATE INDEX IX_musteri_urun_cari
        ON musteri.musteri_urun_kodlari (cari_id);

    PRINT 'musteri.musteri_urun_kodlari tablosu olusturuldu';
END
ELSE
    PRINT 'musteri.musteri_urun_kodlari zaten mevcut';
GO
