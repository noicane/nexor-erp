/*
============================================================
NEXOR ERP - TEST VERiLERi TEMiZLEME SCRiPTi v3.0
============================================================
 Tum FK constraint'leri gecici kapatir
 OBJECT_ID ile tablo varligi kontrol eder
 DELETE + Identity RESEED
 Hata yakalama + rollback
 Detayli raporlama
============================================================
KORUNAN TABLOLAR (silinMEZ):
  tanim.*          - Tum tanim tablolari
  stok.urunler     - Urun kartlari
  stok.urun_*      - Urun tanimlari (fiyat, recete, spec vs.)
  stok.depolar     - Depo tanimlari
  stok.kimyasallar - Kimyasal tanimlari
  sistem.*         - Kullanicilar, roller
  musteri.*        - Cari kartlari
  ik.*             - Personel
  uretim.banyo_tanimlari       - Banyo tanimlari
  uretim.banyo_parametre_tanimlari
  uretim.aski_jigler
  uretim.yuzey_alan_hesaplama
  uretim.kataforez_maliyet
  kalite.olcum_cihazlari       - Cihaz tanimlari
  kalite.kataforez_hata_tipleri - Hata tipi tanimlari
  kalite.giris_kontrol_kriterleri
  kalite.urun_kontrol_gereksinimleri
============================================================
*/

SET NOCOUNT ON;

PRINT '============================================================';
PRINT 'NEXOR ERP - TEST VERILERI TEMIZLEME v3.0';
PRINT '============================================================';
PRINT 'Baslangic: ' + CONVERT(VARCHAR, GETDATE(), 121);
PRINT '';

DECLARE @ErrorCount INT = 0;
DECLARE @TotalDeleted INT = 0;
DECLARE @RowCount INT;

BEGIN TRY
    BEGIN TRANSACTION;

    -- ============================================================
    -- ADIM 1: FK CONSTRAINT'LERI KAPAT
    -- ============================================================
    PRINT 'ADIM 1: FK Constraint''leri kapatiliyor...';
    EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT ALL';
    PRINT '  OK - Tum FK''ler kapatildi';
    PRINT '';

    -- ============================================================
    -- KALITE - Alt tablolar (cocuk FK'ler once)
    -- ============================================================
    PRINT '-- KALITE TABLOLARI ------------------------------------';

    -- Proses kontrol alt tablolari
    IF OBJECT_ID('kalite.etiket_kuyrugu', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.etiket_kuyrugu; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.etiket_kuyrugu              : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.proses_kontrol_hatalar', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.proses_kontrol_hatalar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.proses_kontrol_hatalar      : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.proses_kontrol', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.proses_kontrol; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.proses_kontrol              : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Final kontrol
    IF OBJECT_ID('kalite.kontrol_hatalar', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.kontrol_hatalar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.kontrol_hatalar             : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.kontrol_is_emirleri', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.kontrol_is_emirleri; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.kontrol_is_emirleri         : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.final_kontrol_hatalar', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.final_kontrol_hatalar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.final_kontrol_hatalar       : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.final_kontrol', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.final_kontrol; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.final_kontrol               : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.uretim_redler', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.uretim_redler; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.uretim_redler               : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.red_karar', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.red_karar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.red_karar                   : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Muayene
    IF OBJECT_ID('kalite.muayene_detaylar', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.muayene_detaylar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.muayene_detaylar            : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.muayeneler', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.muayeneler; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.muayeneler                  : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Uygunsuzluk / 8D
    IF OBJECT_ID('kalite.uygunsuzluk_aksiyonlar', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.uygunsuzluk_aksiyonlar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.uygunsuzluk_aksiyonlar      : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.uygunsuzluklar', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.uygunsuzluklar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.uygunsuzluklar              : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Giris kontrol
    IF OBJECT_ID('kalite.giris_kontrol_sonuclari', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.giris_kontrol_sonuclari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.giris_kontrol_sonuclari     : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.giris_kontrol_kayitlari', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.giris_kontrol_kayitlari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.giris_kontrol_kayitlari     : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Kataforez hata kayitlari (tipler degil!)
    IF OBJECT_ID('kalite.kataforez_hata_kayitlari', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.kataforez_hata_kayitlari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.kataforez_hata_kayitlari    : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- SPC
    IF OBJECT_ID('kalite.spc_olcumler', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.spc_olcumler; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.spc_olcumler                : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Test
    IF OBJECT_ID('kalite.test_sonuclari', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.test_sonuclari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.test_sonuclari              : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.test_talep_testler', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.test_talep_testler; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.test_talep_testler          : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.test_talepleri', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.test_talepleri; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.test_talepleri              : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- FMEA
    IF OBJECT_ID('kalite.fmea_ekip', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.fmea_ekip; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.fmea_ekip                   : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.fmea_satirlar', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.fmea_satirlar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.fmea_satirlar               : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.fmea', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.fmea; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.fmea                        : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Kontrol planlari
    IF OBJECT_ID('kalite.kontrol_plan_satirlar', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.kontrol_plan_satirlar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.kontrol_plan_satirlar       : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.kontrol_planlari', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.kontrol_planlari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.kontrol_planlari            : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Kalibrasyon
    IF OBJECT_ID('kalite.kalibrasyon_kayitlari', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.kalibrasyon_kayitlari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.kalibrasyon_kayitlari       : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('kalite.kalibrasyon_planlari', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.kalibrasyon_planlari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.kalibrasyon_planlari        : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- FKK Atama
    IF OBJECT_ID('kalite.fkk_atama', 'U') IS NOT NULL
    BEGIN DELETE FROM kalite.fkk_atama; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  kalite.fkk_atama                   : ' + CAST(@RowCount AS VARCHAR(10)); END

    PRINT '';

    -- ============================================================
    -- SIPARIS - Sevkiyat / Irsaliye / Fatura
    -- ============================================================
    PRINT '-- SIPARIS TABLOLARI -----------------------------------';

    -- Fatura (satirlar once)
    IF OBJECT_ID('siparis.fatura_satirlar', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.fatura_satirlar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.fatura_satirlar            : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('siparis.faturalar', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.faturalar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.faturalar                  : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Cikis irsaliye
    IF OBJECT_ID('siparis.cikis_irsaliye_satirlar', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.cikis_irsaliye_satirlar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.cikis_irsaliye_satirlar    : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('siparis.cikis_irsaliyeleri', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.cikis_irsaliyeleri; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.cikis_irsaliyeleri         : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Giris irsaliye
    IF OBJECT_ID('siparis.giris_irsaliye_satirlar', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.giris_irsaliye_satirlar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.giris_irsaliye_satirlar    : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('siparis.giris_irsaliyeleri', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.giris_irsaliyeleri; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.giris_irsaliyeleri         : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Sevkiyat
    IF OBJECT_ID('siparis.sevkiyat_detaylari', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.sevkiyat_detaylari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.sevkiyat_detaylari         : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('siparis.sevkiyatlar', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.sevkiyatlar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.sevkiyatlar                : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Is emri alt tablolari
    IF OBJECT_ID('siparis.is_emri_stok_hareketi', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.is_emri_stok_hareketi; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.is_emri_stok_hareketi      : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('siparis.is_emri_operasyonlar', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.is_emri_operasyonlar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.is_emri_operasyonlar       : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('siparis.is_emri_lotlar', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.is_emri_lotlar; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.is_emri_lotlar             : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Is emirleri (ana tablo - en son)
    IF OBJECT_ID('siparis.is_emirleri', 'U') IS NOT NULL
    BEGIN DELETE FROM siparis.is_emirleri; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  siparis.is_emirleri                : ' + CAST(@RowCount AS VARCHAR(10)); END

    PRINT '';

    -- ============================================================
    -- STOK TABLOLARI
    -- ============================================================
    PRINT '-- STOK TABLOLARI --------------------------------------';

    IF OBJECT_ID('stok.hareket_event_log', 'U') IS NOT NULL
    BEGIN DELETE FROM stok.hareket_event_log; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  stok.hareket_event_log             : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('stok.hareket_log', 'U') IS NOT NULL
    BEGIN DELETE FROM stok.hareket_log; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  stok.hareket_log                   : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('stok.stok_hareketleri', 'U') IS NOT NULL
    BEGIN DELETE FROM stok.stok_hareketleri; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  stok.stok_hareketleri              : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('stok.depo_cikis', 'U') IS NOT NULL
    BEGIN DELETE FROM stok.depo_cikis; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  stok.depo_cikis                    : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('stok.depo_cikis_emirleri', 'U') IS NOT NULL
    BEGIN DELETE FROM stok.depo_cikis_emirleri; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  stok.depo_cikis_emirleri           : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('stok.lot_durum_gecmisi', 'U') IS NOT NULL
    BEGIN DELETE FROM stok.lot_durum_gecmisi; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  stok.lot_durum_gecmisi             : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('stok.emanet_stok', 'U') IS NOT NULL
    BEGIN DELETE FROM stok.emanet_stok; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  stok.emanet_stok                   : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('stok.stok_bakiye', 'U') IS NOT NULL
    BEGIN DELETE FROM stok.stok_bakiye; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  stok.stok_bakiye                   : ' + CAST(@RowCount AS VARCHAR(10)); END

    PRINT '';

    -- ============================================================
    -- URETIM TABLOLARI
    -- ============================================================
    PRINT '-- URETIM TABLOLARI ------------------------------------';

    -- Vardiya alt tablolari
    IF OBJECT_ID('uretim.vardiya_detay', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.vardiya_detay; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.vardiya_detay               : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('uretim.vardiya_trend', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.vardiya_trend; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.vardiya_trend               : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('uretim.vardiya_uretim', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.vardiya_uretim; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.vardiya_uretim              : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Durus
    IF OBJECT_ID('uretim.durus_kayitlari', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.durus_kayitlari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.durus_kayitlari             : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Ana uretim kayitlari
    IF OBJECT_ID('uretim.bara_takip', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.bara_takip; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.bara_takip                  : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('uretim.uretim_kayitlari', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.uretim_kayitlari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.uretim_kayitlari            : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('uretim.planlama', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.planlama; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.planlama                    : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Sokum (rework)
    IF OBJECT_ID('uretim.sokum_giris', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.sokum_giris; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.sokum_giris                 : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('uretim.sokum_is_emirleri', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.sokum_is_emirleri; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.sokum_is_emirleri           : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- Uretim is emirleri (uretim schema'daki)
    IF OBJECT_ID('uretim.is_emirleri', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.is_emirleri; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.is_emirleri                 : ' + CAST(@RowCount AS VARCHAR(10)); END

    PRINT '';

    -- ============================================================
    -- PLC TABLOLARI (plc_tarihce = ~5M kayit, buyuk!)
    -- ============================================================
    PRINT '-- PLC TABLOLARI ---------------------------------------';

    -- plc_tarihce: ~5M kayit, ayri islem olarak silinecek (bu scriptten haric)
    PRINT '  uretim.plc_tarihce                 : ATLANDI (ayri silinecek)';

    IF OBJECT_ID('uretim.plc_cache', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.plc_cache; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.plc_cache                   : ' + CAST(@RowCount AS VARCHAR(10)); END

    -- plc_sync_durum: sifirla ama silme (1 satir, tekil)
    IF OBJECT_ID('uretim.plc_sync_durum', 'U') IS NOT NULL
    BEGIN
        UPDATE uretim.plc_sync_durum SET son_kaynak_id = 0, toplam_aktarim = 0, son_hata = NULL, son_hata_tarihi = NULL, servis_durumu = 'DURDURULDU';
        PRINT '  uretim.plc_sync_durum              : SIFIRLANDI';
    END

    PRINT '';

    -- ============================================================
    -- LABORATUVAR TABLOLARI
    -- ============================================================
    PRINT '-- LABORATUVAR TABLOLARI --------------------------------';

    IF OBJECT_ID('uretim.banyo_analiz_sonuclari', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.banyo_analiz_sonuclari; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.banyo_analiz_sonuclari      : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('uretim.banyo_takviyeler', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.banyo_takviyeler; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.banyo_takviyeler            : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('uretim.banyo_parametre_log', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.banyo_parametre_log; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.banyo_parametre_log         : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('uretim.lab_event_log', 'U') IS NOT NULL
    BEGIN DELETE FROM uretim.lab_event_log; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  uretim.lab_event_log               : ' + CAST(@RowCount AS VARCHAR(10)); END

    PRINT '';

    -- ============================================================
    -- LOG TABLOLARI
    -- ============================================================
    PRINT '-- LOG TABLOLARI ----------------------------------------';

    IF OBJECT_ID('log.islem_log', 'U') IS NOT NULL
    BEGIN DELETE FROM log.islem_log; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  log.islem_log                      : ' + CAST(@RowCount AS VARCHAR(10)); END

    IF OBJECT_ID('sistem.islem_log', 'U') IS NOT NULL
    BEGIN DELETE FROM sistem.islem_log; SET @RowCount = @@ROWCOUNT; SET @TotalDeleted = @TotalDeleted + @RowCount;
    PRINT '  sistem.islem_log                   : ' + CAST(@RowCount AS VARCHAR(10)); END

    PRINT '';

    -- ============================================================
    -- IDENTITY SEED SIFIRLAMA
    -- ============================================================
    PRINT '-- IDENTITY SEED SIFIRLAMA ------------------------------';

    DECLARE @tbl NVARCHAR(256);
    DECLARE @sql NVARCHAR(512);
    DECLARE @cnt INT;
    DECLARE identity_cursor CURSOR FOR
        SELECT QUOTENAME(s.name) + '.' + QUOTENAME(t.name)
        FROM sys.tables t
        JOIN sys.schemas s ON t.schema_id = s.schema_id
        JOIN sys.identity_columns ic ON t.object_id = ic.object_id
        WHERE s.name IN ('kalite','siparis','stok','uretim','log')
          AND t.name NOT IN ('banyo_tanimlari','banyo_parametre_tanimlari','aski_jigler',
                             'yuzey_alan_hesaplama','kataforez_maliyet','olcum_cihazlari',
                             'kataforez_hata_tipleri','giris_kontrol_kriterleri',
                             'urun_kontrol_gereksinimleri','plc_sync_durum');

    OPEN identity_cursor;
    FETCH NEXT FROM identity_cursor INTO @tbl;
    WHILE @@FETCH_STATUS = 0
    BEGIN
        BEGIN TRY
            SET @sql = N'SELECT @cnt = COUNT(*) FROM ' + @tbl;
            EXEC sp_executesql @sql, N'@cnt INT OUTPUT', @cnt OUTPUT;
            IF @cnt = 0
            BEGIN
                SET @sql = N'DBCC CHECKIDENT (''' + @tbl + ''', RESEED, 0) WITH NO_INFOMSGS;';
                EXEC sp_executesql @sql;
            END
        END TRY
        BEGIN CATCH END CATCH
        FETCH NEXT FROM identity_cursor INTO @tbl;
    END
    CLOSE identity_cursor;
    DEALLOCATE identity_cursor;

    PRINT '  OK - Bos tablolarin identity seed''leri sifirlandi';
    PRINT '';

    -- ============================================================
    -- FK CONSTRAINT'LERI TEKRAR AC
    -- ============================================================
    PRINT 'FK Constraint''leri tekrar aciliyor...';
    EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT ALL';
    PRINT '  OK - Tum FK''ler aktif';
    PRINT '';

    COMMIT TRANSACTION;

    PRINT '============================================================';
    PRINT '  TEMIZLIK TAMAMLANDI!';
    PRINT '  Toplam silinen kayit: ' + CAST(@TotalDeleted AS VARCHAR(10));
    PRINT '============================================================';

END TRY
BEGIN CATCH
    IF @@TRANCOUNT > 0
    BEGIN
        ROLLBACK TRANSACTION;
        PRINT '';
        PRINT '============================================================';
        PRINT '  HATA - Islem geri alindi!';
        PRINT '============================================================';
    END

    PRINT 'Hata Mesaji  : ' + ERROR_MESSAGE();
    PRINT 'Hata Satiri  : ' + CAST(ERROR_LINE() AS VARCHAR(10));
    PRINT 'Hata Numarasi: ' + CAST(ERROR_NUMBER() AS VARCHAR(10));
    PRINT '';

    BEGIN TRY
        EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT ALL';
        PRINT '  OK - FK''ler tekrar aktif (guvenlik)';
    END TRY
    BEGIN CATCH
        PRINT '  ! FK acilirken hata';
    END CATCH

    SET @ErrorCount = 1;
END CATCH;

-- ============================================================
-- KONTROL RAPORU
-- ============================================================
IF @ErrorCount = 0
BEGIN
    PRINT '';
    PRINT '-- KONTROL RAPORU --------------------------------------';
    PRINT '';

    SELECT
        s.name + '.' + t.name AS tablo,
        p.rows AS kayit_sayisi
    FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    JOIN sys.partitions p ON t.object_id = p.object_id AND p.index_id IN (0,1)
    WHERE s.name IN ('kalite','siparis','stok','uretim')
    ORDER BY
        CASE WHEN p.rows > 0 THEN 0 ELSE 1 END,
        s.name, t.name;
END

PRINT '';
PRINT 'Bitis: ' + CONVERT(VARCHAR, GETDATE(), 121);
