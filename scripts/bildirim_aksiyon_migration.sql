-- ============================================================================
-- NEXOR ERP - Bildirim Sistemi & Aksiyonlar Modulu Migration
-- Tarih: 2026-02-18
-- Aciklama: Bildirim sistemini kullanici bazli hale getirir,
--           aksiyonlar modulunu olusturur
-- ============================================================================

USE AtmoLogicERP;
GO

PRINT '=== NEXOR Bildirim & Aksiyon Migration Basliyor ===';
GO

-- ============================================================================
-- 1. sistem.bildirimler - Eksik kolonlari ekle
-- ============================================================================

-- Gonderen kullanici
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirimler') AND name = 'gonderen_id')
BEGIN
    ALTER TABLE sistem.bildirimler ADD gonderen_id BIGINT NULL;
    PRINT '  [+] sistem.bildirimler.gonderen_id eklendi';
END
GO

-- Bildirim tipi (BILGI, UYARI, GOREV, ONAY_BEKLIYOR, HATIRLATMA)
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirimler') AND name = 'tip')
BEGIN
    ALTER TABLE sistem.bildirimler ADD tip NVARCHAR(30) NULL DEFAULT('BILGI');
    PRINT '  [+] sistem.bildirimler.tip eklendi';
END
GO

-- WhatsApp gonderim takibi
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirimler') AND name = 'whatsapp_gonderildi_mi')
BEGIN
    ALTER TABLE sistem.bildirimler ADD whatsapp_gonderildi_mi BIT NULL DEFAULT(0);
    PRINT '  [+] sistem.bildirimler.whatsapp_gonderildi_mi eklendi';
END
GO

IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirimler') AND name = 'whatsapp_gonderim_tarihi')
BEGIN
    ALTER TABLE sistem.bildirimler ADD whatsapp_gonderim_tarihi DATETIME2 NULL;
    PRINT '  [+] sistem.bildirimler.whatsapp_gonderim_tarihi eklendi';
END
GO

-- Sayfa yonlendirme (tiklaninca hangi sayfaya gidecek)
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirimler') AND name = 'sayfa_yonlendirme')
BEGIN
    ALTER TABLE sistem.bildirimler ADD sayfa_yonlendirme NVARCHAR(100) NULL;
    PRINT '  [+] sistem.bildirimler.sayfa_yonlendirme eklendi';
END
GO

-- Guncelleme tarihi
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirimler') AND name = 'guncelleme_tarihi')
BEGIN
    ALTER TABLE sistem.bildirimler ADD guncelleme_tarihi DATETIME2 NULL DEFAULT(GETDATE());
    PRINT '  [+] sistem.bildirimler.guncelleme_tarihi eklendi';
END
GO

-- Foreign key: gonderen_id -> sistem.kullanicilar
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'FK_bildirimler_gonderen')
BEGIN
    ALTER TABLE sistem.bildirimler
    ADD CONSTRAINT FK_bildirimler_gonderen
    FOREIGN KEY (gonderen_id) REFERENCES sistem.kullanicilar(id);
    PRINT '  [+] FK_bildirimler_gonderen eklendi';
END
GO

-- Index: hedef_kullanici_id + okundu_mu (en sik yapilan sorgu)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_bildirimler_hedef_okundu')
BEGIN
    CREATE NONCLUSTERED INDEX IX_bildirimler_hedef_okundu
    ON sistem.bildirimler (hedef_kullanici_id, okundu_mu, aktif_mi)
    INCLUDE (baslik, modul, onem_derecesi, tip, olusturma_tarihi);
    PRINT '  [+] IX_bildirimler_hedef_okundu index eklendi';
END
GO

-- Index: hedef_rol_id
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_bildirimler_hedef_rol')
BEGIN
    CREATE NONCLUSTERED INDEX IX_bildirimler_hedef_rol
    ON sistem.bildirimler (hedef_rol_id, okundu_mu, aktif_mi);
    PRINT '  [+] IX_bildirimler_hedef_rol index eklendi';
END
GO

-- Index: olusturma_tarihi (siralamak icin)
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'IX_bildirimler_tarih')
BEGIN
    CREATE NONCLUSTERED INDEX IX_bildirimler_tarih
    ON sistem.bildirimler (olusturma_tarihi DESC)
    WHERE aktif_mi = 1;
    PRINT '  [+] IX_bildirimler_tarih index eklendi';
END
GO

PRINT '--- sistem.bildirimler guncellendi ---';
GO


-- ============================================================================
-- 2. sistem.bildirim_tanimlari - Eksik kolonlari ekle
-- ============================================================================

-- Sablon mesaj ({urun_adi}, {is_emri_no} gibi placeholder destegi)
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirim_tanimlari') AND name = 'sablon_mesaj')
BEGIN
    ALTER TABLE sistem.bildirim_tanimlari ADD sablon_mesaj NVARCHAR(MAX) NULL;
    PRINT '  [+] sistem.bildirim_tanimlari.sablon_mesaj eklendi';
END
GO

-- Varsayilan hedef rol
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirim_tanimlari') AND name = 'hedef_rol_id')
BEGIN
    ALTER TABLE sistem.bildirim_tanimlari ADD hedef_rol_id BIGINT NULL;
    PRINT '  [+] sistem.bildirim_tanimlari.hedef_rol_id eklendi';
END
GO

-- Otomatik tetikleme
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirim_tanimlari') AND name = 'otomatik_mi')
BEGIN
    ALTER TABLE sistem.bildirim_tanimlari ADD otomatik_mi BIT NULL DEFAULT(0);
    PRINT '  [+] sistem.bildirim_tanimlari.otomatik_mi eklendi';
END
GO

-- Tetikleyici olay kodu
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirim_tanimlari') AND name = 'tetikleyici_olay')
BEGIN
    ALTER TABLE sistem.bildirim_tanimlari ADD tetikleyici_olay NVARCHAR(100) NULL;
    PRINT '  [+] sistem.bildirim_tanimlari.tetikleyici_olay eklendi';
END
GO

-- Varsayilan sayfa yonlendirme
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirim_tanimlari') AND name = 'sayfa_yonlendirme')
BEGIN
    ALTER TABLE sistem.bildirim_tanimlari ADD sayfa_yonlendirme NVARCHAR(100) NULL;
    PRINT '  [+] sistem.bildirim_tanimlari.sayfa_yonlendirme eklendi';
END
GO

PRINT '--- sistem.bildirim_tanimlari guncellendi ---';
GO


-- ============================================================================
-- 3. sistem.bildirim_abonelikleri - Eksik kolonlari ekle
-- ============================================================================

-- WhatsApp bildirim tercihi
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirim_abonelikleri') AND name = 'whatsapp_bildirim')
BEGIN
    ALTER TABLE sistem.bildirim_abonelikleri ADD whatsapp_bildirim BIT NULL DEFAULT(0);
    PRINT '  [+] sistem.bildirim_abonelikleri.whatsapp_bildirim eklendi';
END
GO

-- Minimum onem filtresi
IF NOT EXISTS (SELECT 1 FROM sys.columns WHERE object_id = OBJECT_ID('sistem.bildirim_abonelikleri') AND name = 'minimum_onem')
BEGIN
    ALTER TABLE sistem.bildirim_abonelikleri ADD minimum_onem NVARCHAR(20) NULL DEFAULT('DUSUK');
    PRINT '  [+] sistem.bildirim_abonelikleri.minimum_onem eklendi';
END
GO

PRINT '--- sistem.bildirim_abonelikleri guncellendi ---';
GO


-- ============================================================================
-- 4. sistem.bildirim_tercihleri - Kullanici bazli modul tercihleri
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE schema_id = SCHEMA_ID('sistem') AND name = 'bildirim_tercihleri')
BEGIN
    CREATE TABLE sistem.bildirim_tercihleri (
        id                  BIGINT IDENTITY(1,1) PRIMARY KEY,
        kullanici_id        BIGINT NOT NULL,
        modul               NVARCHAR(50) NOT NULL,         -- KALITE, URETIM, BAKIM, IS_EMIRLERI...
        uygulama_ici        BIT NOT NULL DEFAULT(1),       -- Uygulama ici bildirim alsin mi
        email               BIT NOT NULL DEFAULT(0),       -- Email bildirim alsin mi
        whatsapp            BIT NOT NULL DEFAULT(0),       -- WhatsApp bildirim alsin mi
        minimum_onem        NVARCHAR(20) NOT NULL DEFAULT('DUSUK'), -- KRITIK, YUKSEK, NORMAL, DUSUK
        aktif_mi            BIT NOT NULL DEFAULT(1),
        olusturma_tarihi    DATETIME2 NOT NULL DEFAULT(GETDATE()),
        guncelleme_tarihi   DATETIME2 NOT NULL DEFAULT(GETDATE()),

        CONSTRAINT FK_bildirim_tercihleri_kullanici
            FOREIGN KEY (kullanici_id) REFERENCES sistem.kullanicilar(id),
        CONSTRAINT UQ_bildirim_tercihleri_kullanici_modul
            UNIQUE (kullanici_id, modul)
    );

    CREATE NONCLUSTERED INDEX IX_bildirim_tercihleri_kullanici
    ON sistem.bildirim_tercihleri (kullanici_id, aktif_mi);

    PRINT '  [+] sistem.bildirim_tercihleri tablosu olusturuldu';
END
GO

PRINT '--- Bildirim tablolari tamamlandi ---';
GO


-- ============================================================================
-- 5. sistem.aksiyonlar - Genel amacli aksiyon/gorev takip
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE schema_id = SCHEMA_ID('sistem') AND name = 'aksiyonlar')
BEGIN
    CREATE TABLE sistem.aksiyonlar (
        id                      BIGINT IDENTITY(1,1) PRIMARY KEY,
        uuid                    UNIQUEIDENTIFIER NOT NULL DEFAULT(NEWID()),
        aksiyon_no              NVARCHAR(30) NOT NULL,          -- AKS-2026-00001
        baslik                  NVARCHAR(300) NOT NULL,
        aciklama                NVARCHAR(MAX) NULL,

        -- Kategorilendirme
        kategori                NVARCHAR(30) NOT NULL DEFAULT('GENEL'),
            -- DUZELTICI, ONLEYICI, IYILESTIRME, GENEL
        kaynak_modul            NVARCHAR(50) NULL,              -- KALITE, URETIM, BAKIM, ISG, IK, GENEL
        oncelik                 NVARCHAR(20) NOT NULL DEFAULT('NORMAL'),
            -- KRITIK, YUKSEK, NORMAL, DUSUK

        -- Kaynak iliskilendirme
        kaynak_tablo            NVARCHAR(100) NULL,             -- kalite.uygunsuzluklar, bakim.ariza_bildirimleri vb.
        kaynak_id               BIGINT NULL,                    -- Iliskili kaydin ID'si
        sayfa_yonlendirme       NVARCHAR(100) NULL,             -- Tiklayinca gidecek sayfa

        -- Atama
        sorumlu_id              BIGINT NULL,                    -- FK: ik.personeller
        sorumlu_departman_id    BIGINT NULL,                    -- FK: ik.departmanlar
        talep_eden_id           BIGINT NULL,                    -- FK: ik.personeller

        -- Tarihler
        baslangic_tarihi        DATE NULL,
        hedef_tarih             DATE NULL,
        tamamlanma_tarihi       DATE NULL,
        hatirlatma_tarihi       DATE NULL,                      -- Hatirlatma bildirimi tarihi

        -- Durum
        durum                   NVARCHAR(20) NOT NULL DEFAULT('BEKLIYOR'),
            -- BEKLIYOR, DEVAM_EDIYOR, TAMAMLANDI, DOGRULANDI, IPTAL, GECIKTI
        tamamlanma_orani        INT NOT NULL DEFAULT(0),        -- 0-100

        -- Dogrulama
        dogrulayan_id           BIGINT NULL,                    -- FK: ik.personeller
        dogrulama_tarihi        DATE NULL,
        dogrulama_notu          NVARCHAR(500) NULL,

        -- Etkinlik
        etkinlik_puani          INT NULL,                       -- 1-5
        etkinlik_notu           NVARCHAR(500) NULL,

        -- Sistem alanlari
        aktif_mi                BIT NOT NULL DEFAULT(1),
        olusturma_tarihi        DATETIME2 NOT NULL DEFAULT(GETDATE()),
        guncelleme_tarihi       DATETIME2 NOT NULL DEFAULT(GETDATE()),
        olusturan_id            BIGINT NULL,
        guncelleyen_id          BIGINT NULL,
        silindi_mi              BIT NOT NULL DEFAULT(0),
        silinme_tarihi          DATETIME2 NULL,
        silen_id                BIGINT NULL,

        -- Constraints
        CONSTRAINT UQ_aksiyonlar_uuid UNIQUE (uuid),
        CONSTRAINT UQ_aksiyonlar_no UNIQUE (aksiyon_no),
        CONSTRAINT CHK_aksiyonlar_tamamlanma CHECK (tamamlanma_orani >= 0 AND tamamlanma_orani <= 100),
        CONSTRAINT CHK_aksiyonlar_etkinlik CHECK (etkinlik_puani IS NULL OR (etkinlik_puani >= 1 AND etkinlik_puani <= 5))
    );

    -- Foreign keys
    ALTER TABLE sistem.aksiyonlar ADD CONSTRAINT FK_aksiyonlar_sorumlu
        FOREIGN KEY (sorumlu_id) REFERENCES ik.personeller(id);
    ALTER TABLE sistem.aksiyonlar ADD CONSTRAINT FK_aksiyonlar_departman
        FOREIGN KEY (sorumlu_departman_id) REFERENCES ik.departmanlar(id);
    ALTER TABLE sistem.aksiyonlar ADD CONSTRAINT FK_aksiyonlar_talep_eden
        FOREIGN KEY (talep_eden_id) REFERENCES ik.personeller(id);
    ALTER TABLE sistem.aksiyonlar ADD CONSTRAINT FK_aksiyonlar_dogrulayan
        FOREIGN KEY (dogrulayan_id) REFERENCES ik.personeller(id);
    ALTER TABLE sistem.aksiyonlar ADD CONSTRAINT FK_aksiyonlar_olusturan
        FOREIGN KEY (olusturan_id) REFERENCES sistem.kullanicilar(id);
    ALTER TABLE sistem.aksiyonlar ADD CONSTRAINT FK_aksiyonlar_guncelleyen
        FOREIGN KEY (guncelleyen_id) REFERENCES sistem.kullanicilar(id);

    -- Indexes
    CREATE NONCLUSTERED INDEX IX_aksiyonlar_sorumlu
    ON sistem.aksiyonlar (sorumlu_id, durum, aktif_mi)
    INCLUDE (baslik, oncelik, hedef_tarih)
    WHERE silindi_mi = 0;

    CREATE NONCLUSTERED INDEX IX_aksiyonlar_departman
    ON sistem.aksiyonlar (sorumlu_departman_id, durum, aktif_mi)
    WHERE silindi_mi = 0;

    CREATE NONCLUSTERED INDEX IX_aksiyonlar_durum
    ON sistem.aksiyonlar (durum, hedef_tarih)
    WHERE aktif_mi = 1 AND silindi_mi = 0;

    CREATE NONCLUSTERED INDEX IX_aksiyonlar_kaynak
    ON sistem.aksiyonlar (kaynak_tablo, kaynak_id)
    WHERE silindi_mi = 0;

    CREATE NONCLUSTERED INDEX IX_aksiyonlar_tarih
    ON sistem.aksiyonlar (olusturma_tarihi DESC)
    WHERE aktif_mi = 1 AND silindi_mi = 0;

    PRINT '  [+] sistem.aksiyonlar tablosu olusturuldu';
END
GO


-- ============================================================================
-- 6. sistem.aksiyon_yorumlar - Aksiyon yorum/ilerleme kayitlari
-- ============================================================================

IF NOT EXISTS (SELECT 1 FROM sys.tables WHERE schema_id = SCHEMA_ID('sistem') AND name = 'aksiyon_yorumlar')
BEGIN
    CREATE TABLE sistem.aksiyon_yorumlar (
        id                  BIGINT IDENTITY(1,1) PRIMARY KEY,
        uuid                UNIQUEIDENTIFIER NOT NULL DEFAULT(NEWID()),
        aksiyon_id          BIGINT NOT NULL,
        yorum               NVARCHAR(MAX) NOT NULL,
        yorum_tipi          NVARCHAR(30) NOT NULL DEFAULT('YORUM'),
            -- YORUM, DURUM_DEGISIKLIGI, ILERLEME, DOGRULAMA
        eski_durum          NVARCHAR(20) NULL,                  -- Durum degisikliginde onceki durum
        yeni_durum          NVARCHAR(20) NULL,                  -- Durum degisikliginde yeni durum
        yazan_id            BIGINT NOT NULL,
        olusturma_tarihi    DATETIME2 NOT NULL DEFAULT(GETDATE()),

        CONSTRAINT FK_aksiyon_yorumlar_aksiyon
            FOREIGN KEY (aksiyon_id) REFERENCES sistem.aksiyonlar(id),
        CONSTRAINT FK_aksiyon_yorumlar_yazan
            FOREIGN KEY (yazan_id) REFERENCES sistem.kullanicilar(id),
        CONSTRAINT UQ_aksiyon_yorumlar_uuid UNIQUE (uuid)
    );

    CREATE NONCLUSTERED INDEX IX_aksiyon_yorumlar_aksiyon
    ON sistem.aksiyon_yorumlar (aksiyon_id, olusturma_tarihi DESC);

    PRINT '  [+] sistem.aksiyon_yorumlar tablosu olusturuldu';
END
GO

PRINT '--- Aksiyon tablolari tamamlandi ---';
GO


-- ============================================================================
-- 7. Aksiyon numarasi uretme fonksiyonu
-- ============================================================================

IF OBJECT_ID('sistem.fn_yeni_aksiyon_no', 'FN') IS NOT NULL
    DROP FUNCTION sistem.fn_yeni_aksiyon_no;
GO

CREATE FUNCTION sistem.fn_yeni_aksiyon_no()
RETURNS NVARCHAR(30)
AS
BEGIN
    DECLARE @yil NVARCHAR(4) = CAST(YEAR(GETDATE()) AS NVARCHAR(4));
    DECLARE @son_no INT;

    SELECT @son_no = ISNULL(MAX(
        CAST(RIGHT(aksiyon_no, 5) AS INT)
    ), 0)
    FROM sistem.aksiyonlar
    WHERE aksiyon_no LIKE 'AKS-' + @yil + '-%';

    RETURN 'AKS-' + @yil + '-' + RIGHT('00000' + CAST(@son_no + 1 AS NVARCHAR(5)), 5);
END
GO

PRINT '  [+] sistem.fn_yeni_aksiyon_no fonksiyonu olusturuldu';
GO


-- ============================================================================
-- 8. Bildirim tanimlari - Seed data (varsayilan bildirim sablonlari)
-- ============================================================================

-- Mevcut kayit yoksa ekle
IF NOT EXISTS (SELECT 1 FROM sistem.bildirim_tanimlari WHERE kod = 'IE_YENI')
BEGIN
    INSERT INTO sistem.bildirim_tanimlari (kod, baslik, aciklama, modul, onem_derecesi, bildirim_tipi, aktif_mi, olusturma_tarihi, sablon_mesaj, otomatik_mi, tetikleyici_olay, sayfa_yonlendirme)
    VALUES
    ('IE_YENI', 'Yeni Is Emri', 'Yeni is emri olusturuldu', 'IS_EMIRLERI', 'NORMAL', 'BILGI', 1, GETDATE(), '{is_emri_no} numarali yeni is emri olusturuldu. Musteri: {musteri_adi}', 1, 'IS_EMRI_OLUSTURULDU', 'ie_liste'),
    ('IE_TERMIN_YAKIN', 'Termin Yaklasti', 'Is emri termin tarihi 3 gun icinde', 'IS_EMIRLERI', 'YUKSEK', 'UYARI', 1, GETDATE(), '{is_emri_no} numarali is emrinin termin tarihi {termin_tarih} - 3 gun kaldi!', 1, 'IE_TERMIN_YAKLASTI', 'ie_termin'),
    ('IE_TERMIN_GECTI', 'Termin Gecti', 'Is emri termin tarihi gecti', 'IS_EMIRLERI', 'KRITIK', 'UYARI', 1, GETDATE(), '{is_emri_no} numarali is emrinin termin tarihi ({termin_tarih}) gecmistir!', 1, 'IE_TERMIN_GECTI', 'ie_termin'),
    ('KALITE_UYGUNSUZLUK', 'Uygunsuzluk Acildi', 'Yeni uygunsuzluk kaydi', 'KALITE', 'YUKSEK', 'GOREV', 1, GETDATE(), '{kayit_no} numarali uygunsuzluk acildi. Urun: {urun_adi}', 1, 'UYGUNSUZLUK_ACILDI', 'kalite_red'),
    ('KALITE_KALIBRASYON', 'Kalibrasyon Suresi', 'Kalibrasyon suresi yaklasti/doldu', 'KALITE', 'YUKSEK', 'UYARI', 1, GETDATE(), '{cihaz_adi} cihazinin kalibrasyon suresi {tarih} tarihinde dolacak.', 1, 'KALIBRASYON_YAKLASTI', 'kalite_kalibrasyon'),
    ('BAKIM_ARIZA', 'Ariza Bildirimi', 'Yeni ariza kaydedildi', 'BAKIM', 'KRITIK', 'GOREV', 1, GETDATE(), '{ekipman_adi} icin ariza bildirimi yapildi: {ariza_aciklama}', 1, 'ARIZA_BILDIRILDI', 'bakim_ariza'),
    ('BAKIM_PLAN', 'Bakim Zamani', 'Periyodik bakim zamani geldi', 'BAKIM', 'YUKSEK', 'HATIRLATMA', 1, GETDATE(), '{ekipman_adi} icin planli bakim zamani gelmistir. Plan: {plan_adi}', 1, 'BAKIM_ZAMANI_GELDI', 'bakim_plan'),
    ('STOK_MINIMUM', 'Stok Alarmi', 'Stok minimum seviye altinda', 'STOK', 'KRITIK', 'UYARI', 1, GETDATE(), '{urun_adi} stogu minimum seviyenin altina dustu. Mevcut: {mevcut_stok}, Minimum: {min_stok}', 1, 'STOK_MINIMUM_ALTI', 'depo_stok_takip'),
    ('SEVKIYAT_PLAN', 'Sevkiyat Planlandi', 'Yeni sevkiyat planlandi', 'SEVKIYAT', 'NORMAL', 'BILGI', 1, GETDATE(), '{musteri_adi} icin sevkiyat planlandi. Tarih: {sevk_tarih}', 1, 'SEVKIYAT_PLANLANDI', 'sevk_liste'),
    ('ISG_OLAY', 'ISG Olayi', 'Is guvenligi olayi kaydi', 'ISG', 'KRITIK', 'UYARI', 1, GETDATE(), 'Is guvenligi olayi kaydedildi: {olay_aciklama}. Bolum: {bolum}', 1, 'ISG_OLAY_KAYDEDILDI', 'isg_olay_kayitlari'),
    ('AKSIYON_ATANDI', 'Aksiyon Atandi', 'Size yeni bir aksiyon atandi', 'SISTEM', 'NORMAL', 'GOREV', 1, GETDATE(), '{aksiyon_no} numarali aksiyon size atandi: {baslik}. Hedef tarih: {hedef_tarih}', 1, 'AKSIYON_ATANDI', 'aksiyon_liste'),
    ('AKSIYON_HEDEF_YAKIN', 'Aksiyon Hedef Yaklasti', 'Aksiyon hedef tarihi yaklasti', 'SISTEM', 'YUKSEK', 'HATIRLATMA', 1, GETDATE(), '{aksiyon_no} numarali aksiyonun hedef tarihi ({hedef_tarih}) yaklasti!', 1, 'AKSIYON_HEDEF_YAKLASTI', 'aksiyon_liste'),
    ('AKSIYON_GECIKTI', 'Aksiyon Gecikti', 'Aksiyon hedef tarihi gecti', 'SISTEM', 'KRITIK', 'UYARI', 1, GETDATE(), '{aksiyon_no} numarali aksiyon gecikti! Hedef tarih: {hedef_tarih}', 1, 'AKSIYON_GECIKTI', 'aksiyon_liste'),
    ('ONAY_BEKLIYOR', 'Onay Bekliyor', 'Onayinizi bekleyen kayit var', 'SISTEM', 'YUKSEK', 'ONAY_BEKLIYOR', 1, GETDATE(), '{kayit_tipi} onayinizi bekliyor: {kayit_aciklama}', 1, 'ONAY_GEREKLI', NULL),
    ('SISTEM_DUYURU', 'Sistem Duyurusu', 'Genel sistem duyurusu', 'SISTEM', 'NORMAL', 'BILGI', 1, GETDATE(), '{mesaj}', 0, NULL, NULL);

    PRINT '  [+] Bildirim tanimlari seed data eklendi (15 kayit)';
END
GO


-- ============================================================================
-- 9. Geciken aksiyonlari kontrol eden stored procedure
-- ============================================================================

IF OBJECT_ID('sistem.sp_aksiyon_gecikme_kontrol', 'P') IS NOT NULL
    DROP PROCEDURE sistem.sp_aksiyon_gecikme_kontrol;
GO

CREATE PROCEDURE sistem.sp_aksiyon_gecikme_kontrol
AS
BEGIN
    SET NOCOUNT ON;

    -- Hedef tarihi gecmis ama hala BEKLIYOR/DEVAM_EDIYOR olan aksiyonlari GECIKTI yap
    UPDATE sistem.aksiyonlar
    SET durum = 'GECIKTI',
        guncelleme_tarihi = GETDATE()
    WHERE hedef_tarih < CAST(GETDATE() AS DATE)
      AND durum IN ('BEKLIYOR', 'DEVAM_EDIYOR')
      AND aktif_mi = 1
      AND silindi_mi = 0;

    DECLARE @guncellenen INT = @@ROWCOUNT;

    IF @guncellenen > 0
        PRINT CAST(@guncellenen AS NVARCHAR(10)) + ' aksiyon GECIKTI olarak isaretlendi.';
END
GO

PRINT '  [+] sistem.sp_aksiyon_gecikme_kontrol proseduru olusturuldu';
GO


-- ============================================================================
-- 10. Kullanicinin bildirimlerini getiren view
-- ============================================================================

IF OBJECT_ID('sistem.vw_kullanici_bildirimleri', 'V') IS NOT NULL
    DROP VIEW sistem.vw_kullanici_bildirimleri;
GO

CREATE VIEW sistem.vw_kullanici_bildirimleri
AS
SELECT
    b.id,
    b.uuid,
    b.baslik,
    b.mesaj,
    b.modul,
    b.onem_derecesi,
    b.tip,
    b.kaynak_tablo,
    b.kaynak_id,
    b.sayfa_yonlendirme,
    b.hedef_kullanici_id,
    b.hedef_rol_id,
    b.hedef_departman_id,
    b.gonderen_id,
    b.okundu_mu,
    b.okunma_tarihi,
    b.aktif_mi,
    b.olusturma_tarihi,
    g.ad + ' ' + g.soyad AS gonderen_adi
FROM sistem.bildirimler b
LEFT JOIN sistem.kullanicilar g ON g.id = b.gonderen_id
WHERE b.aktif_mi = 1;
GO

PRINT '  [+] sistem.vw_kullanici_bildirimleri view olusturuldu';
GO


-- ============================================================================
-- 11. Aksiyon ozet view (dashboard icin)
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
    (SELECT COUNT(*) FROM sistem.aksiyon_yorumlar y WHERE y.aksiyon_id = a.id) AS yorum_sayisi
FROM sistem.aksiyonlar a
LEFT JOIN ik.personeller p ON p.id = a.sorumlu_id
LEFT JOIN ik.departmanlar d ON d.id = a.sorumlu_departman_id
LEFT JOIN ik.personeller tp ON tp.id = a.talep_eden_id
WHERE a.silindi_mi = 0 AND a.aktif_mi = 1;
GO

PRINT '  [+] sistem.vw_aksiyon_ozet view olusturuldu';
GO


-- ============================================================================
-- TAMAMLANDI
-- ============================================================================

PRINT '';
PRINT '=== NEXOR Bildirim & Aksiyon Migration TAMAMLANDI ===';
PRINT '';
PRINT 'Olusturulan/guncellenen nesneler:';
PRINT '  Tablolar:';
PRINT '    - sistem.bildirimler (guncellendi: +6 kolon, +3 index)';
PRINT '    - sistem.bildirim_tanimlari (guncellendi: +4 kolon)';
PRINT '    - sistem.bildirim_abonelikleri (guncellendi: +2 kolon)';
PRINT '    - sistem.bildirim_tercihleri (yeni tablo)';
PRINT '    - sistem.aksiyonlar (yeni tablo)';
PRINT '    - sistem.aksiyon_yorumlar (yeni tablo)';
PRINT '  Fonksiyonlar:';
PRINT '    - sistem.fn_yeni_aksiyon_no';
PRINT '  Prosedurler:';
PRINT '    - sistem.sp_aksiyon_gecikme_kontrol';
PRINT '  Viewler:';
PRINT '    - sistem.vw_kullanici_bildirimleri';
PRINT '    - sistem.vw_aksiyon_ozet';
PRINT '  Seed Data:';
PRINT '    - 15 bildirim tanimi (bildirim_tanimlari)';
GO
