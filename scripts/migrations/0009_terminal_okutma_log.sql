-- =============================================
-- NEXOR ERP Migration 0009 - Terminal Okutma Log
-- =============================================
-- El terminalinde sevkiyat icin okutulan lotlari kalici saklar.
-- API restart'ta veya eszamanli kullanimda cache cakismasi olmaz.
-- =============================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'sevkiyat')
    EXEC('CREATE SCHEMA sevkiyat');
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'sevkiyat' AND t.name = 'terminal_okutma_log'
)
BEGIN
    CREATE TABLE sevkiyat.terminal_okutma_log (
        id            BIGINT IDENTITY(1,1) PRIMARY KEY,
        irsaliye_id   BIGINT       NOT NULL,
        lot_no_norm   NVARCHAR(200) NOT NULL,    -- normalize edilmis (-SEV/-SEVK siyrik, UPPER)
        lot_no_raw    NVARCHAR(200) NOT NULL,    -- terminale okutulan ham deger
        satir_id      BIGINT       NULL,         -- esleyen cikis_irsaliye_satirlar.id
        urun_id       BIGINT       NULL,
        kullanici_id  BIGINT       NOT NULL,
        zaman         DATETIME2(0) NOT NULL DEFAULT SYSDATETIME(),
        kaynak        NVARCHAR(20) NOT NULL DEFAULT 'TERMINAL',  -- TERMINAL, MANUEL, ZORLA
        CONSTRAINT FK_terminal_okutma_log_irsaliye
            FOREIGN KEY (irsaliye_id)
            REFERENCES siparis.cikis_irsaliyeleri(id)
    );

    -- Aramalar irsaliye_id + lot uzerinden gider
    CREATE INDEX IX_terminal_okutma_log_irs_lot
        ON sevkiyat.terminal_okutma_log (irsaliye_id, lot_no_norm);

    CREATE INDEX IX_terminal_okutma_log_zaman
        ON sevkiyat.terminal_okutma_log (zaman DESC);

    PRINT 'sevkiyat.terminal_okutma_log tablosu olusturuldu';
END
ELSE
    PRINT 'sevkiyat.terminal_okutma_log zaten mevcut';
GO
