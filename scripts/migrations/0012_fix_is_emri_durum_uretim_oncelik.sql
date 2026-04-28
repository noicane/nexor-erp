-- =============================================================================
-- Migration 0012: sp_is_emri_durum_tazele - URETIMDE oncelikli mantik
-- =============================================================================
-- Bug: uretilen < toplam ama sevk > 0 ise SP "KISMI_SEVK" dusuruyordu.
-- Bu durumda is emri uretim ekranindan kayboluyor (filter URETIMDE/KALITE_BEKLIYOR).
-- 17 IE etkilenmisti.
--
-- Yeni mantik (oncelik sirasi):
--   uretilen >= toplam (uretim bitti):
--      sevk >= toplam       -> SEVK_EDILDI
--      sevk > 0             -> KISMI_SEVK
--      kontrol >= toplam    -> ONAYLANDI / REDDEDILDI / KISMI_RED
--      default              -> URETIMDE (uretim bitti kalite bekliyor)
--   uretilen < toplam (hala uretiliyor):
--      uretilen > 0         -> URETIMDE
--      mevcut = 'PLANLI'    -> PLANLI
--      default              -> BEKLIYOR
--
-- Etkilenmis 17 IE icin sp_is_emri_durum_tazele tek tek cagrilir
-- (SP yeni mantikla durum yeniden hesaplar, dogru olana dusurur).
-- =============================================================================

SET NOCOUNT ON;
GO

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

    IF @mevcut_durum IS NULL RETURN;
    IF @mevcut_durum IN (N'IPTAL', N'IPTAL_EDILDI', N'ARSIV') RETURN;
    IF @toplam <= 0 RETURN;

    DECLARE @yeni_durum NVARCHAR(20);

    IF @uretilen >= @toplam
    BEGIN
        -- Uretim tamamlanmis: sevk/kalite hesabi
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
        ELSE
            SET @yeni_durum = N'URETIMDE';   -- uretim bitti, kalite/sevk bekliyor
    END
    ELSE
    BEGIN
        -- Uretim devam ediyor (uretilen < toplam): kismi sevk olsa bile URETIMDE
        IF @uretilen > 0 OR @kontrol > 0
            SET @yeni_durum = N'URETIMDE';
        ELSE IF @mevcut_durum = N'PLANLI'
            SET @yeni_durum = N'PLANLI';
        ELSE
            SET @yeni_durum = N'BEKLIYOR';
    END

    IF @yeni_durum <> @mevcut_durum
        UPDATE siparis.is_emirleri
           SET durum = @yeni_durum,
               guncelleme_tarihi = GETDATE()
         WHERE id = @is_emri_id;
END
GO

-- ---------------------------------------------------------------------------
-- Etkilenmis 17 IE'yi yeniden hesapla (yeni SP mantigi dogru olana dusurur)
-- ---------------------------------------------------------------------------
DECLARE @ie_id BIGINT;
DECLARE ie_cur CURSOR LOCAL FAST_FORWARD FOR
    SELECT id FROM siparis.is_emirleri
     WHERE durum = N'KISMI_SEVK'
       AND uretilen_miktar < toplam_miktar
       AND silindi_mi = 0;

OPEN ie_cur;
FETCH NEXT FROM ie_cur INTO @ie_id;
WHILE @@FETCH_STATUS = 0
BEGIN
    EXEC siparis.sp_is_emri_durum_tazele @ie_id;
    FETCH NEXT FROM ie_cur INTO @ie_id;
END
CLOSE ie_cur;
DEALLOCATE ie_cur;

PRINT N'Migration 0012 OK: sp_is_emri_durum_tazele yeni mantik + etkilenmis IE durum tazelendi';
GO
