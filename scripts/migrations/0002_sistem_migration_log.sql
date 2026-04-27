-- =============================================
-- NEXOR ERP Migration 0002 - Migration Log Tablosu
-- =============================================
-- sistem schema + migration_log tablosu.
-- migration_runner bu tabloya bakarak hangi migration'larin
-- uygulandigini bilir, eksikleri sirayla calistirir.
-- =============================================

IF NOT EXISTS (SELECT 1 FROM sys.schemas WHERE name = 'sistem')
    EXEC('CREATE SCHEMA sistem');
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.tables t
    JOIN sys.schemas s ON t.schema_id = s.schema_id
    WHERE s.name = 'sistem' AND t.name = 'migration_log'
)
BEGIN
    CREATE TABLE sistem.migration_log (
        migration_no    INT             NOT NULL PRIMARY KEY,
        dosya_adi       NVARCHAR(200)   NOT NULL,
        uygulandi_at    DATETIME2       NOT NULL DEFAULT (GETDATE()),
        uygulayan       NVARCHAR(100)   NULL,
        checksum        NVARCHAR(64)    NULL,
        notlar          NVARCHAR(500)   NULL
    );
    PRINT 'sistem.migration_log tablosu olusturuldu';
END
ELSE
    PRINT 'sistem.migration_log zaten mevcut';
GO
