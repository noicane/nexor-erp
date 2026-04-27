-- =============================================
-- NEXOR ERP Migration 0001 - BASELINE
-- =============================================
-- Amac: Mevcut AtmoLogicERP semasini "sifir noktasi" olarak isaretle.
-- Bu migration SADECE migration_log'a kaydedilir; hicbir DDL calistirmaz.
-- Bu dosyadan sonra yapilacak her DB degisikligi numarali migration ile gelir.
--
-- Kritik kural: AtmoLogicERP'nin mevcut tablolarina/yapilarina
-- ASLA dokunulmayacak. Sadece yeni tablolar eklenir.
-- =============================================

-- Bilgilendirme amacli, hicbir sey yapmaz
PRINT 'Migration 0001 (baseline) uygulandi - mevcut sema sifir noktasi olarak isaretlendi';
GO
