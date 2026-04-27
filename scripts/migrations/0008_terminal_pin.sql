-- =============================================
-- NEXOR ERP Migration 0008 - Terminal PIN Kolonlari
-- =============================================
-- Android el terminali (EDA51) icin PIN tabanli giris.
-- sistem.kullanicilar.terminal_pin_hash: SHA-256(kullanici_id + salt + PIN)
-- sistem.kullanicilar.terminal_pin_set: PIN tanimli mi flag
-- =============================================

IF COL_LENGTH('sistem.kullanicilar', 'terminal_pin_hash') IS NULL
BEGIN
    ALTER TABLE sistem.kullanicilar
        ADD terminal_pin_hash NVARCHAR(128) NULL,
            terminal_pin_set BIT NOT NULL DEFAULT 0,
            terminal_pin_son_degisim DATETIME2 NULL;
    PRINT 'sistem.kullanicilar.terminal_pin_* kolonlari eklendi';
END
ELSE
    PRINT 'terminal_pin_* kolonlari zaten mevcut';
GO
