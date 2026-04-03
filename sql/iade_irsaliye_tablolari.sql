-- =============================================
-- NEXOR ERP - İade İrsaliye Tabloları
-- Müşteriden geri dönen malzeme takibi
-- =============================================

-- Ana iade irsaliye tablosu
IF NOT EXISTS (SELECT * FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name = 'siparis' AND t.name = 'iade_irsaliyeleri')
BEGIN
    CREATE TABLE siparis.iade_irsaliyeleri (
        id              BIGINT IDENTITY(1,1) NOT NULL,
        uuid            UNIQUEIDENTIFIER NOT NULL DEFAULT (NEWID()),
        iade_no         NVARCHAR(30)    NOT NULL,
        referans_irsaliye_id BIGINT     NULL,       -- Hangi çıkış irsaliyesine referans
        cari_id         BIGINT          NOT NULL,
        tarih           DATE            NOT NULL,
        iade_nedeni     NVARCHAR(500)   NULL,
        arac_plaka      NVARCHAR(15)    NULL,
        sofor_adi       NVARCHAR(100)   NULL,
        teslim_alan     NVARCHAR(100)   NULL,
        durum           NVARCHAR(20)    NOT NULL DEFAULT ('TASLAK'),  -- TASLAK, KABUL_EDILDI, IPTAL
        notlar          NVARCHAR(MAX)   NULL,
        olusturma_tarihi DATETIME2      NOT NULL DEFAULT (GETDATE()),
        guncelleme_tarihi DATETIME2     NOT NULL DEFAULT (GETDATE()),
        olusturan_id    BIGINT          NULL,
        guncelleyen_id  BIGINT          NULL,
        silindi_mi      BIT             NOT NULL DEFAULT (0),
        CONSTRAINT PK_iade_irsaliyeleri PRIMARY KEY (id),
        CONSTRAINT FK_iade_irsaliyeleri_cari FOREIGN KEY (cari_id) REFERENCES musteri.cariler(id),
        CONSTRAINT FK_iade_irsaliyeleri_ref FOREIGN KEY (referans_irsaliye_id) REFERENCES siparis.cikis_irsaliyeleri(id)
    );

    CREATE UNIQUE INDEX UQ_iade_irsaliyeleri_no ON siparis.iade_irsaliyeleri(iade_no);
    CREATE INDEX IX_iade_irsaliyeleri_tarih ON siparis.iade_irsaliyeleri(tarih);
    CREATE INDEX IX_iade_irsaliyeleri_cari ON siparis.iade_irsaliyeleri(cari_id);

    PRINT 'siparis.iade_irsaliyeleri tablosu olusturuldu.';
END
ELSE
    PRINT 'siparis.iade_irsaliyeleri zaten mevcut.';
GO

-- İade irsaliye satırları
IF NOT EXISTS (SELECT * FROM sys.tables t JOIN sys.schemas s ON t.schema_id = s.schema_id WHERE s.name = 'siparis' AND t.name = 'iade_irsaliye_satirlar')
BEGIN
    CREATE TABLE siparis.iade_irsaliye_satirlar (
        id              BIGINT IDENTITY(1,1) NOT NULL,
        irsaliye_id     BIGINT          NOT NULL,
        satir_no        INT             NOT NULL,
        urun_id         BIGINT          NULL,
        stok_kodu       NVARCHAR(50)    NULL,
        stok_adi        NVARCHAR(200)   NULL,
        lot_no          NVARCHAR(50)    NULL,
        miktar          DECIMAL(18,4)   NOT NULL,
        birim           NVARCHAR(20)    NULL DEFAULT ('ADET'),
        iade_nedeni     NVARCHAR(200)   NULL,
        referans_satir_id BIGINT        NULL,       -- Çıkış irsaliye satır referansı
        CONSTRAINT PK_iade_irsaliye_satirlar PRIMARY KEY (id),
        CONSTRAINT FK_iade_satirlar_irsaliye FOREIGN KEY (irsaliye_id) REFERENCES siparis.iade_irsaliyeleri(id),
        CONSTRAINT FK_iade_satirlar_urun FOREIGN KEY (urun_id) REFERENCES stok.urunler(id)
    );

    CREATE INDEX IX_iade_satirlar_irsaliye ON siparis.iade_irsaliye_satirlar(irsaliye_id);

    PRINT 'siparis.iade_irsaliye_satirlar tablosu olusturuldu.';
END
ELSE
    PRINT 'siparis.iade_irsaliye_satirlar zaten mevcut.';
GO
