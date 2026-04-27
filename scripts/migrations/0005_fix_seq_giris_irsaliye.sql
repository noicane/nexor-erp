-- 0005_fix_seq_giris_irsaliye.sql
-- siparis.seq_giris_irsaliye_id, giris_irsaliyeleri tablosundaki suffix'e
-- kiyasla geride kalmis durumda (tabletten fotoyla atan apps/irsaliye_okuyucu
-- eski MAX yolunu kullaniyordu ve sequence'i advance etmiyordu).
-- Sonuc: UNIQUE KEY 'UQ_giris_irsaliyeleri_no' ihlali.
-- Bu migration sequence'i tablodaki gercek max suffix + 1 degerine getirir.

DECLARE @next INT;

SELECT @next = ISNULL(MAX(TRY_CONVERT(INT, RIGHT(irsaliye_no, 4))), 0) + 1
FROM siparis.giris_irsaliyeleri
WHERE irsaliye_no LIKE 'GRS-%';

IF @next IS NULL OR @next < 1
    SET @next = 1;

DECLARE @sql NVARCHAR(200) = N'ALTER SEQUENCE siparis.seq_giris_irsaliye_id RESTART WITH ' + CAST(@next AS NVARCHAR(20));
EXEC sp_executesql @sql;

PRINT 'seq_giris_irsaliye_id yeni degeri: ' + CAST(@next AS NVARCHAR(20));
