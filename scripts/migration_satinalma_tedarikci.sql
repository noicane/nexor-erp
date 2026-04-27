-- satinalma.talepler'e tedarikci_id kolonu ekler (NULL olabilir).
-- Kullanim: SSMS'de calistir. Idempotent — birden fazla calisirsa sorunsuz.

USE AtmoLogicERP;
GO

IF NOT EXISTS (
    SELECT 1 FROM sys.columns
    WHERE object_id = OBJECT_ID('satinalma.talepler')
      AND name = 'tedarikci_id'
)
BEGIN
    ALTER TABLE satinalma.talepler
    ADD tedarikci_id BIGINT NULL;
    PRINT 'tedarikci_id kolonu eklendi';
END
ELSE
BEGIN
    PRINT 'tedarikci_id zaten var';
END
GO

-- FK (musteri.cariler'e)
IF NOT EXISTS (
    SELECT 1 FROM sys.foreign_keys
    WHERE name = 'FK_talepler_tedarikci'
)
BEGIN
    ALTER TABLE satinalma.talepler
    ADD CONSTRAINT FK_talepler_tedarikci
    FOREIGN KEY (tedarikci_id) REFERENCES musteri.cariler(id);
    PRINT 'FK_talepler_tedarikci eklendi';
END
ELSE
BEGIN
    PRINT 'FK_talepler_tedarikci zaten var';
END
GO

-- Dogrulama
SELECT name, system_type_id, is_nullable
FROM sys.columns
WHERE object_id = OBJECT_ID('satinalma.talepler') AND name = 'tedarikci_id';
GO
