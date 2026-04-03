-- =====================================================
-- FINAL KALITE RAPORU SABLONLARI
-- Her kaplama turu icin proses adimlari ve kontrol testleri
-- =====================================================

-- 1) RAPOR SABLONLARI (ana tablo - kaplama turune bagli)
IF NOT EXISTS (SELECT * FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name='kalite' AND t.name='rapor_sablonlari')
BEGIN
    CREATE TABLE kalite.rapor_sablonlari (
        id              BIGINT IDENTITY(1,1) PRIMARY KEY,
        kaplama_turu_id BIGINT NOT NULL,
        sablon_adi      NVARCHAR(200) NOT NULL,
        aciklama        NVARCHAR(500) NULL,
        aktif_mi        BIT NOT NULL DEFAULT 1,
        olusturma_tarihi DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_rapor_sablonlari_kaplama FOREIGN KEY (kaplama_turu_id) REFERENCES tanim.kaplama_turleri(id)
    );
    PRINT 'kalite.rapor_sablonlari olusturuldu';
END
ELSE PRINT 'kalite.rapor_sablonlari zaten mevcut';

-- 2) SABLON ADIMLARI (proses adimlari - sirali)
IF NOT EXISTS (SELECT * FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name='kalite' AND t.name='rapor_sablon_adimlari')
BEGIN
    CREATE TABLE kalite.rapor_sablon_adimlari (
        id              BIGINT IDENTITY(1,1) PRIMARY KEY,
        sablon_id       BIGINT NOT NULL,
        sira            INT NOT NULL,
        adim_adi_tr     NVARCHAR(200) NOT NULL,    -- Turkce baslik
        adim_adi_en     NVARCHAR(200) NULL,        -- Ingilizce baslik
        uygulama_tipi   NVARCHAR(50) NOT NULL,     -- DALDIRMA, PUSKÜRTME, FIRIN
        uygulama_sartlari NVARCHAR(200) NOT NULL,  -- 60-80 DERECE/5-10 DK
        olcu_aleti      NVARCHAR(50) NOT NULL DEFAULT 'ERP',  -- ERP, XRAY, ELCOMETER, GOZ
        CONSTRAINT FK_rapor_sablon_adimlari_sablon FOREIGN KEY (sablon_id) REFERENCES kalite.rapor_sablonlari(id)
    );
    PRINT 'kalite.rapor_sablon_adimlari olusturuldu';
END
ELSE PRINT 'kalite.rapor_sablon_adimlari zaten mevcut';

-- 3) SABLON KONTROLLER (kalinlik, gorunum, cross-cut vb.)
IF NOT EXISTS (SELECT * FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name='kalite' AND t.name='rapor_sablon_kontroller')
BEGIN
    CREATE TABLE kalite.rapor_sablon_kontroller (
        id              BIGINT IDENTITY(1,1) PRIMARY KEY,
        sablon_id       BIGINT NOT NULL,
        sira            INT NOT NULL,
        kontrol_adi_tr  NVARCHAR(200) NOT NULL,
        kontrol_adi_en  NVARCHAR(200) NULL,
        karakteristik   NVARCHAR(100) NULL,         -- ELCOMETER, 9.57405, LEK-16 vb.
        aciklama_tr     NVARCHAR(500) NULL,          -- Tolerans/aciklama metni
        aciklama_en     NVARCHAR(500) NULL,
        olcu_aleti      NVARCHAR(50) NOT NULL,       -- XRAY, ELCOMETER, GOZ
        birim           NVARCHAR(20) NULL,            -- MICRON vb.
        tolerans_min    DECIMAL(10,2) NULL,
        tolerans_max    DECIMAL(10,2) NULL,
        deger_girilir_mi BIT NOT NULL DEFAULT 0,     -- 1 = kalinlik olcumu gibi deger girilecek
        CONSTRAINT FK_rapor_sablon_kontroller_sablon FOREIGN KEY (sablon_id) REFERENCES kalite.rapor_sablonlari(id)
    );
    PRINT 'kalite.rapor_sablon_kontroller olusturuldu';
END
ELSE PRINT 'kalite.rapor_sablon_kontroller zaten mevcut';

-- 4) RAPOR KAYITLARI (uretilen raporlar - lot bazli)
IF NOT EXISTS (SELECT * FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name='kalite' AND t.name='final_kalite_raporlari')
BEGIN
    CREATE TABLE kalite.final_kalite_raporlari (
        id              BIGINT IDENTITY(1,1) PRIMARY KEY,
        rapor_no        NVARCHAR(20) NOT NULL,
        sablon_id       BIGINT NOT NULL,
        irsaliye_id     BIGINT NULL,
        is_emri_id      BIGINT NULL,
        lot_no          NVARCHAR(50) NOT NULL,
        miktar          DECIMAL(18,2) NULL,
        birim           NVARCHAR(10) NULL DEFAULT 'AD',
        kalinlik_olcumleri NVARCHAR(200) NULL,      -- JSON veya virgul ayrilmis degerler
        kontrol_eden    NVARCHAR(100) NULL,
        onaylayan       NVARCHAR(100) NULL,
        sonuc           NVARCHAR(20) NOT NULL DEFAULT 'UYGUN',  -- UYGUN / UYGUN DEGIL
        rapor_tarihi    DATETIME NOT NULL DEFAULT GETDATE(),
        olusturma_tarihi DATETIME NOT NULL DEFAULT GETDATE(),
        CONSTRAINT FK_fkr_sablon FOREIGN KEY (sablon_id) REFERENCES kalite.rapor_sablonlari(id)
    );
    PRINT 'kalite.final_kalite_raporlari olusturuldu';
END
ELSE PRINT 'kalite.final_kalite_raporlari zaten mevcut';


-- =====================================================
-- SEED DATA
-- =====================================================

-- Mevcut kayit kontrolu
IF NOT EXISTS (SELECT 1 FROM kalite.rapor_sablonlari)
BEGIN
    PRINT 'Seed data yukleniyor...';

    -- =========== KATAFOREZ (kaplama_turu_id=1) ===========
    INSERT INTO kalite.rapor_sablonlari (kaplama_turu_id, sablon_adi) VALUES (1, N'Kataforez Final Kalite Raporu');
    DECLARE @ktf_id BIGINT = SCOPE_IDENTITY();

    -- Proses adimlari
    INSERT INTO kalite.rapor_sablon_adimlari (sablon_id, sira, adim_adi_tr, adim_adi_en, uygulama_tipi, uygulama_sartlari) VALUES
    (@ktf_id, 1, N'SICAK YAĞ ALMA',           N'HOT OIL DEGREASING',            N'DALDIRMA', N'60-80 DERECE/5-10 DK'),
    (@ktf_id, 2, N'ASİDİK YAĞ ALMA',          N'ACIDIC OIL DEGREASING',         N'DALDIRMA', N'ODA SICAKLIĞI/ 5-10 DK'),
    (@ktf_id, 3, N'ELEKTRİKLİ YAĞ ALMA',      N'ELECTRIAL OIL DEGREASING',      N'DALDIRMA', N'ODA SICAKLIĞI /1-3 DK'),
    (@ktf_id, 4, N'AKTİVASYON',                N'ACTIVATION',                    N'DALDIRMA', N'PH8-10.5 / 2 DK'),
    (@ktf_id, 5, N'FOSFAT KAPLAMA',            N'PHOSPHATTING',                  N'DALDIRMA', N'47-50 DERECE /2-5 DK'),
    (@ktf_id, 6, N'PASİVASYON',                N'PASSIVATION',                   N'DALDIRMA', N'PH 4.2-4.8/ 2DK'),
    (@ktf_id, 7, N'KATAFOREZ KAPLAMA',         N'CATAPHORESIS COATING',          N'DALDIRMA', N'28-30DERECE/2-15DK'),
    (@ktf_id, 8, N'UF DURULAMA 1-2',           N'UF RINSE',                      N'DALDIRMA', N'PH 5-5.8/1-2 DK'),
    (@ktf_id, 9, N'KURUTMA',                   N'DRYING',                        N'FIRIN',    N'200 DERECE/ 20-30DK');

    -- Kontroller
    INSERT INTO kalite.rapor_sablon_kontroller (sablon_id, sira, kontrol_adi_tr, kontrol_adi_en, karakteristik, aciklama_tr, aciklama_en, olcu_aleti, birim, tolerans_min, tolerans_max, deger_girilir_mi) VALUES
    (@ktf_id, 1, N'KAPLAMA KALINLIĞI', N'COATING THICKNESS', N'ELCOMETER', N'MICRON', N'MICRON', N'XRAY', N'MICRON', 15, 25, 1),
    (@ktf_id, 2, N'GÖRÜNÜM KONTROLÜ', N'VIEW CONTROL', N'9.57405', N'KARARMA VE AKMA OLMAMALIDIR. YÜZEY GÖRÜNÜMÜ TEK DÜZE OLMALIDIR.', N'ALL SURFACE MUST COATED IT MUST NOT', N'GÖZ', NULL, NULL, NULL, 0),
    (@ktf_id, 3, N'CROSS CUT TESTİ', N'CROSS CUT TEST', N'LEK-16', N'BAZ METALDEN AYRIŞMA OLMAMALIDIR.', N'DO NOT DISTRIBUTE FROM BASE METAL', N'GÖZ', NULL, NULL, NULL, 0);


    -- =========== CINKO NIKEL (kaplama_turu_id=3) ===========
    INSERT INTO kalite.rapor_sablonlari (kaplama_turu_id, sablon_adi) VALUES (3, N'Çinko Nikel Final Kalite Raporu');
    DECLARE @znni_id BIGINT = SCOPE_IDENTITY();

    INSERT INTO kalite.rapor_sablon_adimlari (sablon_id, sira, adim_adi_tr, adim_adi_en, uygulama_tipi, uygulama_sartlari) VALUES
    (@znni_id, 1, N'SICAK YAĞ ALMA',                  N'HOT OIL DEGREASING',              N'DALDIRMA', N'60-80 DERECE/5-10 DK'),
    (@znni_id, 2, N'ASİDİK YAĞ ALMA',                 N'ACIDIC OIL DEGREASING',           N'DALDIRMA', N'ODA SICAKLIĞI/ 5-10 DK'),
    (@znni_id, 3, N'ELEKTRİKLİ YAĞ ALMA',             N'ELECTRIAL OIL DEGREASING',        N'DALDIRMA', N'ODA SICAKLIĞI /1-3 DK'),
    (@znni_id, 4, N'ALKALİ ÇİNKO NİKEL KAPLAMA',      N'ALKALINE ZINC NIKEL COATING',     N'DALDIRMA', N'18-34 DERECE'),
    (@znni_id, 5, N'PASİVASYON',                       N'PASSIVATION',                     N'DALDIRMA', N'ODA SICAKLIĞI/ PH2-3'),
    (@znni_id, 6, N'LAK',                              N'SEALING',                         N'DALDIRMA', N'ODA SICAKLIĞI / PH 9-10'),
    (@znni_id, 7, N'KURUTMA',                          N'DRYING',                          N'FIRIN',    N'50-100 DERECE/ 20-30DK');

    INSERT INTO kalite.rapor_sablon_kontroller (sablon_id, sira, kontrol_adi_tr, kontrol_adi_en, karakteristik, aciklama_tr, aciklama_en, olcu_aleti, birim, tolerans_min, tolerans_max, deger_girilir_mi) VALUES
    (@znni_id, 1, N'KAPLAMA KALINLIĞI', N'COATING THICKNESS', N'XRAY /ELCOMETER', N'MICRON', N'MICRON', N'XRAY', N'MICRON', 10, 16, 1),
    (@znni_id, 2, N'GÖRÜNÜM KONTROLÜ', N'VIEW CONTROL', N'9.57405', N'KARARMA VE AKMA OLMAMALIDIR. YÜZEY GÖRÜNÜMÜ TEK DÜZE OLMALIDIR.', N'ALL SURFACE MUST COATED IT MUST NOT', N'GÖZ', NULL, NULL, NULL, 0),
    (@znni_id, 3, N'YAPIŞMA TESTİ', N'ADHESION TEST', N'LEK-14', N'BAZ METALDEN AYRIŞMA OLMAMALIDIR.', N'DO NOT DISTRIBUTE FROM BASE METAL', N'GÖZ', NULL, NULL, NULL, 0),
    (@znni_id, 4, N'CR+3 TESPİTİ', N'DETERMINATION OF CR+3', N'LEK-15', N'CR+6 OLMAMALIDIR.', N'SHOULD BE NO CR+6', N'GÖZ', NULL, NULL, NULL, 0);


    -- =========== CINKO (kaplama_turu_id=2) ===========
    -- Cinko, Cinko Nikel ile ayni proses (kullanici onayina gore degisebilir)
    INSERT INTO kalite.rapor_sablonlari (kaplama_turu_id, sablon_adi) VALUES (2, N'Çinko Final Kalite Raporu');
    DECLARE @zn_id BIGINT = SCOPE_IDENTITY();

    INSERT INTO kalite.rapor_sablon_adimlari (sablon_id, sira, adim_adi_tr, adim_adi_en, uygulama_tipi, uygulama_sartlari) VALUES
    (@zn_id, 1, N'SICAK YAĞ ALMA',                  N'HOT OIL DEGREASING',              N'DALDIRMA', N'60-80 DERECE/5-10 DK'),
    (@zn_id, 2, N'ASİDİK YAĞ ALMA',                 N'ACIDIC OIL DEGREASING',           N'DALDIRMA', N'ODA SICAKLIĞI/ 5-10 DK'),
    (@zn_id, 3, N'ELEKTRİKLİ YAĞ ALMA',             N'ELECTRIAL OIL DEGREASING',        N'DALDIRMA', N'ODA SICAKLIĞI /1-3 DK'),
    (@zn_id, 4, N'ALKALİ ÇİNKO NİKEL KAPLAMA',      N'ALKALINE ZINC NIKEL COATING',     N'DALDIRMA', N'18-34 DERECE'),
    (@zn_id, 5, N'PASİVASYON',                       N'PASSIVATION',                     N'DALDIRMA', N'ODA SICAKLIĞI/ PH2-3'),
    (@zn_id, 6, N'LAK',                              N'SEALING',                         N'DALDIRMA', N'ODA SICAKLIĞI / PH 9-10'),
    (@zn_id, 7, N'KURUTMA',                          N'DRYING',                          N'FIRIN',    N'50-100 DERECE/ 20-30DK');

    INSERT INTO kalite.rapor_sablon_kontroller (sablon_id, sira, kontrol_adi_tr, kontrol_adi_en, karakteristik, aciklama_tr, aciklama_en, olcu_aleti, birim, tolerans_min, tolerans_max, deger_girilir_mi) VALUES
    (@zn_id, 1, N'KAPLAMA KALINLIĞI', N'COATING THICKNESS', N'XRAY /ELCOMETER', N'MICRON', N'MICRON', N'XRAY', N'MICRON', 10, 16, 1),
    (@zn_id, 2, N'GÖRÜNÜM KONTROLÜ', N'VIEW CONTROL', N'9.57405', N'KARARMA VE AKMA OLMAMALIDIR. YÜZEY GÖRÜNÜMÜ TEK DÜZE OLMALIDIR.', N'ALL SURFACE MUST COATED IT MUST NOT', N'GÖZ', NULL, NULL, NULL, 0),
    (@zn_id, 3, N'YAPIŞMA TESTİ', N'ADHESION TEST', N'LEK-14', N'BAZ METALDEN AYRIŞMA OLMAMALIDIR.', N'DO NOT DISTRIBUTE FROM BASE METAL', N'GÖZ', NULL, NULL, NULL, 0),
    (@zn_id, 4, N'CR+3 TESPİTİ', N'DETERMINATION OF CR+3', N'LEK-15', N'CR+6 OLMAMALIDIR.', N'SHOULD BE NO CR+6', N'GÖZ', NULL, NULL, NULL, 0);


    -- =========== TOZ BOYA (kaplama_turu_id=4) ===========
    INSERT INTO kalite.rapor_sablonlari (kaplama_turu_id, sablon_adi) VALUES (4, N'Toz Boya Final Kalite Raporu');
    DECLARE @toz_id BIGINT = SCOPE_IDENTITY();

    INSERT INTO kalite.rapor_sablon_adimlari (sablon_id, sira, adim_adi_tr, adim_adi_en, uygulama_tipi, uygulama_sartlari) VALUES
    (@toz_id, 1, N'SICAK YAĞ ALMA',       N'HOT OIL DEGREASING',  N'PÜSKÜRTME', N'60-80 DERECE/5-10 DK'),
    (@toz_id, 2, N'FOSFAT KAPLAMA',        N'PHOSPHATTING',        N'PÜSKÜRTME', N'47-50 DERECE /2-5 DK'),
    (@toz_id, 3, N'DURULAMA',              N'RINSE',               N'PÜSKÜRTME', N'PH 4.2-4.8/ 2DK'),
    (@toz_id, 4, N'KURUTMA',               N'DRYING',              N'FIRIN',     N'100 DERECE /2-15DK'),
    (@toz_id, 5, N'TOZ BOYA',              N'POWDER COATING',      N'PÜSKÜRTME', N'PH 5-5.8/1-2 DK'),
    (@toz_id, 6, N'FIRIN',                 N'BAKERY',              N'FIRIN',     N'200 DERECE/ 20-30DK');

    INSERT INTO kalite.rapor_sablon_kontroller (sablon_id, sira, kontrol_adi_tr, kontrol_adi_en, karakteristik, aciklama_tr, aciklama_en, olcu_aleti, birim, tolerans_min, tolerans_max, deger_girilir_mi) VALUES
    (@toz_id, 1, N'KAPLAMA KALINLIĞI', N'COATING THICKNESS', N'ELCOMETER', N'MICRON', N'MICRON', N'ELCOMETER', N'MICRON', 60, 120, 1),
    (@toz_id, 2, N'GÖRÜNÜM KONTROLÜ', N'VIEW CONTROL', N'9.57405', N'KARARMA VE AKMA OLMAMALIDIR. YÜZEY GÖRÜNÜMÜ TEK DÜZE OLMALIDIR.', N'ALL SURFACE MUST COATED IT MUST NOT', N'GÖZ', NULL, NULL, NULL, 0);

    PRINT 'Seed data yuklendi: KTF, ZN, ZNNI, TOZ BOYA';
END
ELSE PRINT 'Seed data zaten mevcut';
