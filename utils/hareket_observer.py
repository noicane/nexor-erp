# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Hareket Observer (Genişletilmiş)
Stok hareketleri ve laboratuvar eventlerini kaydeder
"""


class HareketObserver:
    """Event kaydedici - HareketMotoru'na dokunmaz"""
    
    def __init__(self, conn):
        self.conn = conn
        self.cursor = conn.cursor()
    
    def on_hareket_completed(self, lot_no, depo_id, miktar=0, event_tipi=None):
        """
        Hareket tamamlandı - event kaydet
        
        Args:
            lot_no: Lot numarası veya BANYO-X
            depo_id: Hedef depo ID (None olabilir)
            miktar: Miktar (opsiyonel)
            event_tipi: Manuel event tipi (opsiyonel) - LAB için kullan
        """
        try:
            # Event tipini belirle
            if event_tipi:
                # Manuel event tipi verilmiş (LAB için)
                final_event_tipi = event_tipi
            elif depo_id:
                # Depo koduna göre otomatik belirle
                self.cursor.execute("""
                    SELECT kod FROM tanim.depolar WHERE id = ?
                """, (depo_id,))
                row = self.cursor.fetchone()
                depo_kod = row[0] if row else ''
                final_event_tipi = self._determine_event_type(depo_kod, lot_no)
            else:
                # Depo yok, lot_no'ya göre tahmin et
                final_event_tipi = self._determine_event_from_lot(lot_no)
            
            # Event kaydı oluştur
            self.cursor.execute("""
                INSERT INTO stok.hareket_event_log 
                (lot_no, event_tipi, depo_id, miktar, event_durumu)
                VALUES (?, ?, ?, ?, 'BEKLIYOR')
            """, (lot_no, final_event_tipi, depo_id, miktar))
            
            print(f"✅ Event kaydedildi: {lot_no} → {final_event_tipi}")
        
        except Exception as e:
            print(f"⚠️ Observer hatası: {e}")
    
    def _determine_event_type(self, depo_kod: str, lot_no: str) -> str:
        """Depo koduna göre event tipini belirle"""
        depo_kod = depo_kod.upper() if depo_kod else ''
        
        if 'KAB' in depo_kod or 'KABUL' in depo_kod:
            return 'GIRIS_KONTROL_GEREKLI'
        elif 'FKK' in depo_kod or 'FINAL' in depo_kod:
            return 'FINAL_KONTROL_TAMAMLANDI'
        elif 'RED' in depo_kod:
            return 'RED_KARAR_VERILDI'
        elif 'SEV' in depo_kod or 'SEVK' in depo_kod:
            return 'SEVK_HAZIR'
        elif 'SOKUM' in depo_kod or 'XI' in depo_kod:
            return 'SOKUM_BASLADI'
        elif 'KAR' in depo_kod or 'KARANTINA' in depo_kod:
            return 'KARANTINA_BEKLIYOR'
        else:
            return 'TRANSFER_TAMAMLANDI'
    
    def _determine_event_from_lot(self, lot_no: str) -> str:
        """Lot numarasından event tipini tahmin et"""
        lot_no = lot_no.upper() if lot_no else ''
        
        if 'BANYO' in lot_no:
            return 'LAB_ANALIZ_TAMAMLANDI'
        elif 'SEV' in lot_no:
            return 'SEVK_HAZIR'
        elif 'RED' in lot_no:
            return 'RED_KARAR_VERILDI'
        else:
            return 'GIRIS_KONTROL_GEREKLI'
    
    def on_lab_analiz(self, banyo_id: int, durum: str):
        """
        Laboratuvar analizi tamamlandı - özel event
        
        Args:
            banyo_id: Banyo ID
            durum: NORMAL / UYARI / KRITIK
        """
        event_tipi_map = {
            'NORMAL': 'LAB_ANALIZ_NORMAL',
            'UYARI': 'LAB_ANALIZ_UYARI',
            'KRITIK': 'LAB_ANALIZ_KRITIK'
        }
        
        self.on_hareket_completed(
            lot_no=f"BANYO-{banyo_id}",
            depo_id=None,
            miktar=0,
            event_tipi=event_tipi_map.get(durum, 'LAB_ANALIZ_TAMAMLANDI')
        )
