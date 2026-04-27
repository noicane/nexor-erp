-- 0006_resync_seq_giris_irsaliye.sql
-- 0005 sequence'i tablodaki max suffix+1'e cekmisti, ancak depo_kabul.py ve
-- apps/irsaliye_okuyucu/server.py icindeki try/except fallback dali bazi
-- kayitlari sequence'i advance etmeden yazmis. Sonuc: sequence yine geride.
-- 2026-04-25 14:32 itibariyle MAX suffix=478, sequence current_value=469.
--
-- Kod yolundaki fallback kaldirildi (sadece SEQUENCE birakildi). Bu migration
-- sequence'i tabloyla yeniden senkronlar.
--
-- 0005 ile ozdes mantik; idempotent (her zaman MAX suffix+1'e RESTART eder).

DECLARE @next INT;

SELECT @next = ISNULL(MAX(TRY_CONVERT(INT, RIGHT(irsaliye_no, 4))), 0) + 1
FROM siparis.giris_irsaliyeleri
WHERE irsaliye_no LIKE 'GRS-%';

IF @next IS NULL OR @next < 1
    SET @next = 1;

DECLARE @sql NVARCHAR(200) = N'ALTER SEQUENCE siparis.seq_giris_irsaliye_id RESTART WITH ' + CAST(@next AS NVARCHAR(20));
EXEC sp_executesql @sql;

PRINT 'seq_giris_irsaliye_id yeni degeri: ' + CAST(@next AS NVARCHAR(20));
