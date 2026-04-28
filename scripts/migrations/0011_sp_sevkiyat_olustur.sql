-- =============================================================================
-- Migration 0011: sp_sevkiyat_olustur + sp_is_emri_durum_tazele
-- =============================================================================
-- Hedef: modules/sevkiyat/sevk_yeni.py::_irsaliye_olustur mantigini SP'ye tasi
--        Hem desktop hem terminal_api ayni SP'yi cagirsin (tek dogruluk kaynagi)
--
-- DB: SQL Server 2014 (compat 120) -> OPENJSON YOK, STRING_AGG YOK
-- Cozum: lotlar_xml XML parametresi + STUFF/FOR XML PATH agregasyonu
--
-- Yapilanlar:
--   1) siparis.sp_is_emri_durum_tazele - IE durumunu yeniden hesaplar
--   2) siparis.sp_sevkiyat_olustur     - Tek cari icin sevkiyat olusturur
--      - cari fallback (LIKE musteri_adi -> herhangi aktif cari)
--      - irsaliye_no (tanim.numara_tanimlari, yil bazli reset, nexor max sync)
--      - INSERT cikis_irsaliyeleri (durum=HAZIRLANDI)
--      - INSERT cikis_irsaliye_satirlar (stok_kodu bazinda grupla, lot_no birlestir)
--      - UPDATE stok_bakiye (miktar dus, kalite_durumu = SEVK_EDILDI eger 0)
--      - INSERT stok_hareketleri (CIKIS / SEVKIYAT, ref=IRSALIYE/irsaliye_id)
--      - sp_is_emri_durum_tazele her unique IE icin
--
-- Girdi (XML format):
--   <lotlar>
--     <lot lot_no="LOT-X" miktar="10" cari_id="5" is_emri_id="42" stok_kodu="K1" />
--     ...
--   </lotlar>
--
-- Output:
--   @irsaliye_id BIGINT, @irsaliye_no NVARCHAR(30)
-- =============================================================================

SET NOCOUNT ON;
GO

-- =============================================================================
-- HELPER: sp_is_emri_durum_tazele
-- =============================================================================
IF OBJECT_ID('siparis.sp_is_emri_durum_tazele', 'P') IS NOT NULL
    DROP PROCEDURE siparis.sp_is_emri_durum_tazele;
GO

CREATE PROCEDURE siparis.sp_is_emri_durum_tazele
    @is_emri_id BIGINT
AS
BEGIN
    SET NOCOUNT ON;

    DECLARE @mevcut_durum NVARCHAR(20),
            @toplam DECIMAL(18,4),
            @uretilen DECIMAL(18,4),
            @kontrol DECIMAL(18,4),
            @saglam DECIMAL(18,4),
            @hatali DECIMAL(18,4),
            @sevk DECIMAL(18,4);

    SELECT @mevcut_durum = ie.durum,
           @toplam = ISNULL(ie.toplam_miktar, 0),
           @uretilen = ISNULL(ie.uretilen_miktar, 0),
           @kontrol = ISNULL((SELECT SUM(fk.kontrol_miktar) FROM kalite.final_kontrol fk
                              WHERE fk.is_emri_id = ie.id), 0),
           @saglam = ISNULL((SELECT SUM(fk.saglam_adet) FROM kalite.final_kontrol fk
                             WHERE fk.is_emri_id = ie.id), 0),
           @hatali = ISNULL((SELECT SUM(fk.hatali_adet) FROM kalite.final_kontrol fk
                             WHERE fk.is_emri_id = ie.id), 0),
           @sevk = ISNULL((SELECT SUM(sat.miktar)
                           FROM siparis.cikis_irsaliye_satirlar sat
                           LEFT JOIN siparis.cikis_irsaliyeleri ci ON sat.irsaliye_id = ci.id
                           WHERE sat.is_emri_id = ie.id
                             AND ISNULL(ci.durum, '') <> 'IPTAL'), 0)
      FROM siparis.is_emirleri ie
     WHERE ie.id = @is_emri_id;

    -- IE bulunmadiysa cik
    IF @mevcut_durum IS NULL RETURN;

    -- Korunan durumlar (dokunma)
    IF @mevcut_durum IN (N'IPTAL', N'IPTAL_EDILDI', N'ARSIV') RETURN;

    -- Toplam 0 ise karar verilemez
    IF @toplam <= 0 RETURN;

    DECLARE @yeni_durum NVARCHAR(20);

    IF @sevk >= @toplam
        SET @yeni_durum = N'SEVK_EDILDI';
    ELSE IF @sevk > 0
        SET @yeni_durum = N'KISMI_SEVK';
    ELSE IF @kontrol >= @toplam
    BEGIN
        IF @hatali = 0 SET @yeni_durum = N'ONAYLANDI';
        ELSE IF @saglam = 0 SET @yeni_durum = N'REDDEDILDI';
        ELSE SET @yeni_durum = N'KISMI_RED';
    END
    ELSE IF @kontrol > 0 OR @uretilen > 0
        SET @yeni_durum = N'URETIMDE';
    ELSE IF @mevcut_durum = N'PLANLI'
        SET @yeni_durum = N'PLANLI';
    ELSE
        SET @yeni_durum = N'BEKLIYOR';

    -- Degisiklik yoksa UPDATE atma (log temizligi)
    IF @yeni_durum <> @mevcut_durum
        UPDATE siparis.is_emirleri
           SET durum = @yeni_durum,
               guncelleme_tarihi = GETDATE()
         WHERE id = @is_emri_id;
END
GO


-- =============================================================================
-- ANA SP: sp_sevkiyat_olustur
-- =============================================================================
IF OBJECT_ID('siparis.sp_sevkiyat_olustur', 'P') IS NOT NULL
    DROP PROCEDURE siparis.sp_sevkiyat_olustur;
GO

CREATE PROCEDURE siparis.sp_sevkiyat_olustur
    @cari_id        BIGINT,
    @musteri_adi    NVARCHAR(400),
    @tasiyici       NVARCHAR(100) = NULL,
    @plaka          NVARCHAR(15)  = NULL,
    @sofor          NVARCHAR(100) = NULL,
    @notlar         NVARCHAR(MAX) = NULL,
    @lotlar_xml     XML,                  -- <lotlar><lot lot_no=".." miktar=".." cari_id=".." is_emri_id=".." stok_kodu=".." /></lotlar>
    @kullanici_id   BIGINT = NULL,
    @irsaliye_id    BIGINT OUTPUT,
    @irsaliye_no    NVARCHAR(30) OUTPUT
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRY
        BEGIN TRANSACTION;

        -- ---------------------------------------------------------------------
        -- 1) Lotlari XML'den oku
        -- ---------------------------------------------------------------------
        DECLARE @lotlar TABLE (
            lot_no      NVARCHAR(50),
            miktar      DECIMAL(18,4),
            cari_id     BIGINT,
            is_emri_id  BIGINT,
            stok_kodu   NVARCHAR(100)
        );

        INSERT INTO @lotlar (lot_no, miktar, cari_id, is_emri_id, stok_kodu)
        SELECT
            x.value('@lot_no',     'NVARCHAR(50)'),
            x.value('@miktar',     'DECIMAL(18,4)'),
            x.value('@cari_id',    'BIGINT'),
            x.value('@is_emri_id', 'BIGINT'),
            x.value('@stok_kodu',  'NVARCHAR(100)')
          FROM @lotlar_xml.nodes('/lotlar/lot') AS T(x);

        IF NOT EXISTS (SELECT 1 FROM @lotlar)
            THROW 50001, N'En az bir lot gerekli', 1;

        -- is_emri_id NOT NULL constraint - eksik IE'li lot var mi?
        IF EXISTS (SELECT 1 FROM @lotlar WHERE is_emri_id IS NULL)
            THROW 50002, N'Lotlardan birinde is_emri_id eksik', 1;

        -- ---------------------------------------------------------------------
        -- 2) Cari fallback (cari_id yoksa LIKE arama, sonra herhangi aktif)
        -- ---------------------------------------------------------------------
        IF @cari_id IS NULL OR NOT EXISTS (SELECT 1 FROM musteri.cariler WHERE id = @cari_id)
        BEGIN
            DECLARE @arama NVARCHAR(20) = LEFT(ISNULL(@musteri_adi, N''), 20);
            IF LEN(@arama) > 0
                SELECT TOP 1 @cari_id = id FROM musteri.cariler
                 WHERE (unvan LIKE N'%' + @arama + N'%' OR kisa_ad LIKE N'%' + @arama + N'%')
                   AND aktif_mi = 1;

            IF @cari_id IS NULL
                SELECT TOP 1 @cari_id = id FROM musteri.cariler WHERE aktif_mi = 1;

            IF @cari_id IS NULL
                THROW 50003, N'Aktif cari bulunamadi', 1;
        END

        -- ---------------------------------------------------------------------
        -- 3) Irsaliye numarasi uret (tanim.numara_tanimlari + nexor max sync)
        -- ---------------------------------------------------------------------
        DECLARE @prefix NVARCHAR(20), @ayirici NVARCHAR(5),
                @basamak INT, @son_no INT,
                @yil_bazli BIT, @aktif_yil INT, @tanim_id BIGINT;

        SELECT @tanim_id = id, @prefix = prefix, @ayirici = ayirici,
               @basamak = basamak_sayisi, @son_no = son_numara,
               @yil_bazli = yil_bazli_mi, @aktif_yil = aktif_yil
          FROM tanim.numara_tanimlari
         WHERE kod = N'IRSALIYE' AND aktif_mi = 1;

        IF @tanim_id IS NULL
        BEGIN
            -- Tanim yok: hardcoded fallback
            SET @prefix = N'IRS';
            SET @ayirici = N'-';
            SET @basamak = 6;
            SELECT @son_no = ISNULL(MAX(TRY_CAST(SUBSTRING(irsaliye_no, 5, 10) AS INT)), 0)
              FROM siparis.cikis_irsaliyeleri
             WHERE irsaliye_no LIKE N'IRS-%';
        END
        ELSE
        BEGIN
            -- Yil bazli sifirlama
            IF @yil_bazli = 1 AND @aktif_yil < YEAR(GETDATE())
            BEGIN
                SET @son_no = 0;
                UPDATE tanim.numara_tanimlari
                   SET aktif_yil = YEAR(GETDATE()), son_numara = 0,
                       guncelleme_tarihi = GETDATE()
                 WHERE id = @tanim_id;
            END

            -- Nexor fiili max ile sync (drift onleme - feedback_seq_no_fallback)
            DECLARE @pattern NVARCHAR(50) = @prefix + @ayirici + N'%';
            DECLARE @skip_len INT = LEN(@prefix) + LEN(@ayirici) + 1;
            DECLARE @nexor_max INT;
            SELECT @nexor_max = ISNULL(MAX(TRY_CAST(SUBSTRING(irsaliye_no, @skip_len, 20) AS INT)), 0)
              FROM siparis.cikis_irsaliyeleri
             WHERE irsaliye_no LIKE @pattern;
            IF @nexor_max > @son_no SET @son_no = @nexor_max;
        END

        DECLARE @yeni_no INT = @son_no + 1;
        SET @irsaliye_no = @prefix + @ayirici
            + RIGHT(REPLICATE(N'0', @basamak) + CAST(@yeni_no AS NVARCHAR(20)), @basamak);

        IF @tanim_id IS NOT NULL
            UPDATE tanim.numara_tanimlari
               SET son_numara = @yeni_no, guncelleme_tarihi = GETDATE()
             WHERE id = @tanim_id;

        -- ---------------------------------------------------------------------
        -- 4) Irsaliye INSERT (durum=HAZIRLANDI)
        -- ---------------------------------------------------------------------
        INSERT INTO siparis.cikis_irsaliyeleri
            (uuid, irsaliye_no, cari_id, tarih, sevk_tarihi,
             tasiyici_firma, arac_plaka, sofor_adi,
             durum, notlar,
             olusturma_tarihi, guncelleme_tarihi, silindi_mi, olusturan_id)
        VALUES
            (NEWID(), @irsaliye_no, @cari_id, CAST(GETDATE() AS DATE), GETDATE(),
             @tasiyici, @plaka, @sofor,
             N'HAZIRLANDI', @notlar,
             GETDATE(), GETDATE(), 0, @kullanici_id);

        SET @irsaliye_id = SCOPE_IDENTITY();

        -- ---------------------------------------------------------------------
        -- 5) Satirlari yaz: stok_kodu bazinda grupla, lot_no_birlestir
        --    SQL Server 2014 -> STRING_AGG yerine STUFF + FOR XML PATH
        -- ---------------------------------------------------------------------
        DECLARE @gruplar TABLE (
            stok_kodu   NVARCHAR(100),
            grup_miktar DECIMAL(18,4),
            ie_id       BIGINT,
            lot_listesi NVARCHAR(MAX),
            urun_id     BIGINT
        );

        ;WITH grup_tmp AS (
            SELECT ISNULL(stok_kodu, N'') AS stok_kodu,
                   SUM(miktar) AS grup_miktar,
                   MIN(is_emri_id) AS ie_id
              FROM @lotlar
             GROUP BY ISNULL(stok_kodu, N'')
        )
        INSERT INTO @gruplar (stok_kodu, grup_miktar, ie_id, lot_listesi)
        SELECT g.stok_kodu, g.grup_miktar, g.ie_id,
               STUFF((
                   SELECT N', ' + l2.lot_no
                     FROM @lotlar l2
                    WHERE ISNULL(l2.stok_kodu, N'') = g.stok_kodu
                      AND l2.lot_no IS NOT NULL
                      FOR XML PATH(''), TYPE
               ).value('.', 'NVARCHAR(MAX)'), 1, 2, N'')
          FROM grup_tmp g;

        -- urun_id cozumle (stok_kodu -> stok.urunler.id)
        UPDATE g
           SET urun_id = u.id
          FROM @gruplar g
          OUTER APPLY (
              SELECT TOP 1 id FROM stok.urunler
               WHERE urun_kodu = g.stok_kodu AND aktif_mi = 1
          ) u;

        -- urun_id bulunmayanlar icin herhangi aktif urun (desktop fallback)
        UPDATE g
           SET urun_id = (SELECT TOP 1 id FROM stok.urunler WHERE aktif_mi = 1)
          FROM @gruplar g
         WHERE g.urun_id IS NULL;

        IF EXISTS (SELECT 1 FROM @gruplar WHERE urun_id IS NULL)
            THROW 50004, N'Aktif urun bulunamadi (urunler tablosu bos)', 1;

        DECLARE @satir_no INT = 0;
        DECLARE @stok_kodu NVARCHAR(100), @grup_miktar DECIMAL(18,4),
                @grup_ie BIGINT, @grup_lots NVARCHAR(MAX), @grup_urun BIGINT;

        DECLARE grup_cur CURSOR LOCAL FAST_FORWARD FOR
            SELECT stok_kodu, grup_miktar, ie_id, lot_listesi, urun_id FROM @gruplar;

        OPEN grup_cur;
        FETCH NEXT FROM grup_cur INTO @stok_kodu, @grup_miktar, @grup_ie, @grup_lots, @grup_urun;

        WHILE @@FETCH_STATUS = 0
        BEGIN
            SET @satir_no = @satir_no + 1;

            INSERT INTO siparis.cikis_irsaliye_satirlar
                (uuid, irsaliye_id, satir_no, is_emri_id, urun_id, miktar, birim_id, lot_no)
            VALUES
                (NEWID(), @irsaliye_id, @satir_no, @grup_ie, @grup_urun, @grup_miktar, 1, @grup_lots);

            FETCH NEXT FROM grup_cur INTO @stok_kodu, @grup_miktar, @grup_ie, @grup_lots, @grup_urun;
        END
        CLOSE grup_cur;
        DEALLOCATE grup_cur;

        -- ---------------------------------------------------------------------
        -- 6) Stok cikisi her lot icin (motor.stok_cikis esdegeri)
        -- ---------------------------------------------------------------------
        DECLARE @lot_no NVARCHAR(50), @lot_miktar DECIMAL(18,4), @lot_ie BIGINT;
        DECLARE @bakiye_id BIGINT, @bakiye_urun_id BIGINT,
                @bakiye_depo_id BIGINT, @bakiye_miktar DECIMAL(18,4);

        DECLARE lot_cur CURSOR LOCAL FAST_FORWARD FOR
            SELECT lot_no, miktar, is_emri_id FROM @lotlar;

        OPEN lot_cur;
        FETCH NEXT FROM lot_cur INTO @lot_no, @lot_miktar, @lot_ie;

        WHILE @@FETCH_STATUS = 0
        BEGIN
            -- Bakiyeyi bul (lot_no -> stok_bakiye)
            SET @bakiye_id = NULL;
            SELECT TOP 1
                   @bakiye_id = id, @bakiye_urun_id = urun_id,
                   @bakiye_depo_id = depo_id, @bakiye_miktar = miktar
              FROM stok.stok_bakiye
             WHERE lot_no = @lot_no;

            IF @bakiye_id IS NULL
            BEGIN
                DECLARE @err1 NVARCHAR(200) = N'Lot bulunamadi: ' + @lot_no;
                THROW 50005, @err1, 1;
            END

            IF @lot_miktar > @bakiye_miktar
            BEGIN
                DECLARE @err2 NVARCHAR(200) = N'Yetersiz stok lot=' + @lot_no;
                THROW 50006, @err2, 1;
            END

            DECLARE @yeni_miktar DECIMAL(18,4) = @bakiye_miktar - @lot_miktar;

            -- Bakiye guncelle
            UPDATE stok.stok_bakiye
               SET miktar = @yeni_miktar,
                   kalite_durumu = CASE WHEN @yeni_miktar = 0
                                        THEN N'SEVK_EDILDI'
                                        ELSE kalite_durumu END,
                   son_hareket_tarihi = GETDATE()
             WHERE id = @bakiye_id;

            -- Hareket kaydi (CIKIS / SEVKIYAT, miktar negatif)
            INSERT INTO stok.stok_hareketleri
                (uuid, hareket_tipi, hareket_nedeni, tarih,
                 urun_id, depo_id, miktar, birim_id, lot_no,
                 referans_tip, referans_id, aciklama,
                 olusturma_tarihi, olusturan_id)
            VALUES
                (NEWID(), N'CIKIS', N'SEVKIYAT', GETDATE(),
                 @bakiye_urun_id, @bakiye_depo_id, -@lot_miktar, 1, @lot_no,
                 N'IRSALIYE', @irsaliye_id,
                 N'Sevkiyat cikisi - ' + @irsaliye_no,
                 GETDATE(), @kullanici_id);

            FETCH NEXT FROM lot_cur INTO @lot_no, @lot_miktar, @lot_ie;
        END
        CLOSE lot_cur;
        DEALLOCATE lot_cur;

        -- ---------------------------------------------------------------------
        -- 7) IE durum tazele (her unique IE icin)
        -- ---------------------------------------------------------------------
        DECLARE @ie_uniq BIGINT;
        DECLARE ie_cur CURSOR LOCAL FAST_FORWARD FOR
            SELECT DISTINCT is_emri_id FROM @lotlar WHERE is_emri_id IS NOT NULL;
        OPEN ie_cur;
        FETCH NEXT FROM ie_cur INTO @ie_uniq;
        WHILE @@FETCH_STATUS = 0
        BEGIN
            EXEC siparis.sp_is_emri_durum_tazele @ie_uniq;
            FETCH NEXT FROM ie_cur INTO @ie_uniq;
        END
        CLOSE ie_cur;
        DEALLOCATE ie_cur;

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;
        THROW;
    END CATCH
END
GO

PRINT N'Migration 0011 OK: siparis.sp_is_emri_durum_tazele + siparis.sp_sevkiyat_olustur olusturuldu';
GO
