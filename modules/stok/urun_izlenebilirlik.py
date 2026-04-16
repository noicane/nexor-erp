# -*- coding: utf-8 -*-
"""
REDLINE NEXOR ERP - Ürün İzlenebilirlik v4.2
Sol: QTreeWidget - parent lot tek satır, expand ile alt lotlar
Sağ: 14 adımlı timeline + kompakt onay matrisi
"""

import traceback
from datetime import datetime, date
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QWidget, QScrollArea, QGridLayout,
    QSplitter, QTreeWidget, QTreeWidgetItem, QAbstractItemView,
    QHeaderView
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QBrush

from components.base_page import BasePage
from core.database import get_db_connection
from core.nexor_brand import brand


def get_style(theme=None):
    return {
        'card_bg':  brand.BG_CARD,
        'input_bg': brand.BG_INPUT,
        'border':   brand.BORDER,
        'text':     brand.TEXT,
        'text2':    brand.TEXT_MUTED,
        'muted':    brand.TEXT_DIM,
        'primary':  brand.PRIMARY,
        'ok':       brand.SUCCESS,
        'warn':     brand.WARNING,
        'err':      brand.ERROR,
        'info':     brand.INFO,
    }


STEP_CFG = {
    'is_emri':         {'icon': '📋', 'label': 'İş Emri'},
    'giris_irsaliye':  {'icon': '🧾', 'label': 'Giriş İrsaliye'},
    'mal_kabul':       {'icon': '📦', 'label': 'Mal Kabul'},
    'depo_hareket':    {'icon': '📥', 'label': 'Depo Hareket'},
    'giris_kalite':    {'icon': '🔬', 'label': 'Giriş Kalite Kontrol'},
    'planlama':        {'icon': '📅', 'label': 'Üretim Planlama'},
    'bara_takip':      {'icon': '⚙️', 'label': 'Bara Takip'},
    'banyo_analiz':    {'icon': '🧪', 'label': 'Banyo Analiz'},
    'ilk_urun':        {'icon': '🔧', 'label': 'İlk Ürün Onayı (FR.75)'},
    'sokum':           {'icon': '🏭', 'label': 'Söküm & Hat Çıkış'},
    'final_kontrol':   {'icon': '✅', 'label': 'Final Kontrol (FKK)'},
    'red_uygunsuzluk': {'icon': '⚠️', 'label': 'Red / Uygunsuzluk'},
    'sevkiyat':        {'icon': '🚚', 'label': 'Sevkiyat & Çıkış İrsaliye'},
    'musteri_sikayet': {'icon': '📞', 'label': 'Müşteri Şikayeti'},
}

ST_CLR = lambda s: {'completed': s['ok'], 'warning': s['warn'], 'failed': s['err'], 'active': s['info'], 'pending': s['muted']}
ST_BG = {'completed': 'rgba(16,185,129,0.06)', 'warning': 'rgba(245,158,11,0.06)', 'failed': 'rgba(239,68,68,0.08)', 'active': 'rgba(59,130,246,0.06)', 'pending': 'rgba(255,255,255,0.02)'}
POS = ('ONAY','ONAYLANDI','KABUL','TAMAMLANDI','KAPALI','OLUŞTURULDU','GİRİŞ')
NEG = ('RED','REDDEDILDI','IPTAL')


def rcol(r, s):
    if r in POS: return s['ok']
    if r in NEG: return s['err']
    return s['warn'] if r in ('KOSULLU','KISMI','ACIK','DEVAM') else s['text2']


# ═══════════════════════════════════════════════════════════════
class TimelineStepWidget(QFrame):
    def __init__(self, key, data, s, parent=None):
        super().__init__(parent)
        cfg = STEP_CFG.get(key, {'icon': '❓', 'label': key})
        st = data.get('status', 'pending')
        ac = ST_CLR(s).get(st, s['muted'])
        bg = ST_BG.get(st, 'rgba(255,255,255,0.02)')
        self.setStyleSheet(f"TimelineStepWidget {{ background: {bg}; border: 1px solid {ac}33; border-left: 3px solid {ac}; border-radius: 8px; margin: 0 0 0 28px; }}")
        m = QVBoxLayout(self); m.setContentsMargins(14, 10, 14, 10); m.setSpacing(6)
        h = QHBoxLayout(); h.setSpacing(8)
        il = QLabel(cfg['icon']); il.setStyleSheet("font-size:16px; background:transparent; border:none;"); h.addWidget(il)
        tl = QLabel(cfg['label']); tl.setStyleSheet(f"font-size:12px; font-weight:700; color:{ac}; background:transparent; border:none;"); h.addWidget(tl)
        cnt = data.get('count', 1)
        if cnt > 1:
            cl = QLabel(f"({cnt})"); cl.setStyleSheet(f"color:{s['muted']}; font-size:10px; background:transparent; border:none;"); h.addWidget(cl)
        h.addStretch()
        bt = data.get('status_text', '')
        if bt:
            bl = QLabel(bt); bl.setStyleSheet(f"background:{ac}22; color:{ac}; border:1px solid {ac}44; border-radius:10px; padding:2px 10px; font-size:9px; font-weight:600;"); h.addWidget(bl)
        tarih = data.get('tarih')
        if tarih:
            ts = tarih.strftime('%d.%m.%Y %H:%M') if isinstance(tarih, datetime) else (tarih.strftime('%d.%m.%Y') if isinstance(tarih, date) else str(tarih))
            dl = QLabel(ts); dl.setStyleSheet(f"color:{s['muted']}; font-size:10px; background:transparent; border:none;"); h.addWidget(dl)
        m.addLayout(h)
        det = data.get('detay', [])
        if det:
            g = QGridLayout(); g.setContentsMargins(24,0,0,0); g.setHorizontalSpacing(16); g.setVerticalSpacing(2)
            cols = 3 if len(det) > 4 else 2
            for i,(k,v) in enumerate(det):
                l = QLabel(f"<span style='color:{s['muted']};font-size:10px;'>{k}:</span> <span style='color:{s['text']};font-size:10px;font-weight:500;'>{v}</span>")
                l.setStyleSheet("background:transparent; border:none;"); l.setTextFormat(Qt.RichText)
                g.addWidget(l, i//cols, i%cols)
            m.addLayout(g)
        onay = data.get('onay_bilgi')
        if onay:
            sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setStyleSheet(f"background:{s['border']}; border:none; max-height:1px; margin:2px 24px;"); m.addWidget(sep)
            ol = QHBoxLayout(); ol.setContentsMargins(24,0,0,0); ol.setSpacing(16)
            for info in onay:
                rc = rcol(info.get('result',''), s)
                txt = f"{info.get('icon','👤')} <span style='color:{s['muted']};font-size:9px;'>{info.get('role','')}</span> <span style='color:{s['text']};font-size:10px;font-weight:600;'>{info.get('name','-')}</span>"
                if info.get('result'): txt += f"  <span style='color:{rc};font-size:9px;font-weight:700;'>● {info['result']}</span>"
                pl = QLabel(txt); pl.setTextFormat(Qt.RichText); pl.setStyleSheet("background:transparent; border:none;"); ol.addWidget(pl)
            ol.addStretch(); m.addLayout(ol)


class TimelineConnector(QWidget):
    def __init__(self, color, is_last=False, parent=None):
        super().__init__(parent)
        self._c = QColor(color); self._l = is_last; self.setFixedWidth(28); self.setMinimumHeight(40)
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); cx = self.width()//2
        if not self._l: p.setPen(QPen(QColor('#333333'),2)); p.drawLine(cx,14,cx,self.height())
        p.setPen(Qt.NoPen); p.setBrush(QBrush(self._c)); p.drawEllipse(cx-5,3,10,10)
        if self._c != QColor('#666666'): p.setBrush(QBrush(QColor('#1A1A1A'))); p.drawEllipse(cx-2,6,4,4)
        p.end()


class ApprovalMatrixWidget(QFrame):
    def __init__(self, approvals, s, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"ApprovalMatrixWidget {{ background:{s['card_bg']}; border:1px solid {s['border']}; border-radius:6px; }}")
        lo = QVBoxLayout(self); lo.setContentsMargins(10,5,10,5); lo.setSpacing(2)
        if not approvals: return
        flow = QHBoxLayout(); flow.setSpacing(4); flow.setContentsMargins(0,0,0,0)
        hdr = QLabel("👥"); hdr.setStyleSheet("font-size:11px; background:transparent; border:none;"); flow.addWidget(hdr)
        for a in approvals:
            rc = rcol(a.get('result',''), s)
            person = (a.get('person','-') or '-').split(' ')[0]
            step_s = a.get('step','')[:12]
            tag = QLabel(f"<span style='color:{s['muted']};font-size:8px;'>{step_s}</span> <span style='color:{s['text']};font-size:9px;'>{person}</span> <span style='color:{rc};font-size:8px;font-weight:700;'>●</span>")
            tag.setTextFormat(Qt.RichText)
            tag.setStyleSheet(f"background:{rc}0D; border:1px solid {rc}33; border-radius:3px; padding:1px 5px;")
            flow.addWidget(tag)
        flow.addStretch(); lo.addLayout(flow)


# ═══════════════════════════════════════════════════════════════
# MAIN PAGE
# ═══════════════════════════════════════════════════════════════
class UrunIzlenebilirlikPage(BasePage):
    def __init__(self, theme: dict):
        try:
            super().__init__(theme)
            self.s = get_style(theme)
            self._setup_ui()
            QTimer.singleShot(300, self._load_kayitlar)
        except Exception as e:
            print(f"[İZLENEBİLİRLİK INIT HATASI] {e}")
            traceback.print_exc()

    def _fmt(self, v):
        if v is None: return '-'
        try: return f"{v:,.0f}"
        except Exception: return str(v)

    def _fmtd(self, v, d=1):
        if v is None: return '-'
        try: return f"{v:,.{d}f}"
        except Exception: return str(v)

    def _clear(self, lo):
        while lo.count():
            c = lo.takeAt(0)
            w = c.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            elif c.layout():
                self._clear(c.layout())

    def _get_parent_lot(self, lot_no):
        if not lot_no: return lot_no
        parts = lot_no.rsplit('-', 1)
        if len(parts) == 2 and parts[1].isdigit() and len(parts[1]) <= 3:
            return parts[0]
        return lot_no

    def _setup_ui(self):
        s = self.s
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(8)

        # ── HEADER ──
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet(f"QFrame {{ background:{s['card_bg']}; border:1px solid {s['border']}; border-radius:8px; }}")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(12, 0, 12, 0)
        hl.setSpacing(12)

        ti = QLabel("🔍 Ürün İzlenebilirlik")
        ti.setStyleSheet(f"font-size:14px; font-weight:600; color:{s['text']};")
        hl.addWidget(ti)

        self.arama_tipi = QComboBox()
        self.arama_tipi.setFixedHeight(28)
        self.arama_tipi.setFixedWidth(130)
        self.arama_tipi.setStyleSheet(f"QComboBox {{ background:{s['input_bg']}; border:1px solid {s['border']}; border-radius:4px; padding:0 8px; color:{s['text']}; font-size:11px; }}")
        self.arama_tipi.addItems(["Lot No", "Stok Kodu", "İş Emri No"])
        hl.addWidget(self.arama_tipi)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Lot no, stok kodu veya iş emri no...")
        self.search_input.setFixedHeight(28)
        self.search_input.setFixedWidth(300)
        self.search_input.setStyleSheet(f"background:{s['input_bg']}; border:1px solid {s['border']}; border-radius:4px; padding:0 8px; color:{s['text']}; font-size:11px;")
        self.search_input.returnPressed.connect(self._search)
        hl.addWidget(self.search_input)

        btn = QPushButton("Ara")
        btn.setFixedSize(60, 28)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"QPushButton {{ background:{s['primary']}; color:white; border:none; border-radius:4px; font-size:11px; font-weight:600; }} QPushButton:hover {{ background:#b91c1c; }}")
        btn.clicked.connect(self._search)
        hl.addWidget(btn)
        hl.addStretch()

        self.stat_labels = {}
        for key, icon, color in [('toplam', '📦', s['text2']), ('ok', '✅', s['ok']), ('wip', '🔄', s['warn'])]:
            l = QLabel(f"{icon} 0")
            l.setStyleSheet(f"color:{color}; font-size:12px; font-weight:600;")
            self.stat_labels[key] = l
            hl.addWidget(l)
        layout.addWidget(header)

        # ── SPLITTER ──
        sp = QSplitter(Qt.Horizontal)
        sp.setStyleSheet(f"QSplitter::handle {{ background:{s['border']}; width:2px; }}")

        # LEFT: QTreeWidget
        lf = QFrame()
        lf.setStyleSheet(f"QFrame {{ background:{s['card_bg']}; border:1px solid {s['border']}; border-radius:8px; }}")
        ll = QVBoxLayout(lf)
        ll.setContentsMargins(0, 0, 0, 0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Lot / Alt Lot", "Stok Kodu", "Durum"])
        self.tree.setColumnCount(3)
        self.tree.header().setStretchLastSection(False)
        self.tree.header().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.tree.setRootIsDecorated(True)
        self.tree.setAnimated(True)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{ background:{s['input_bg']}; color:{s['text']}; border:none; font-size:11px; outline:none; }}
            QTreeWidget::item {{ padding:5px 4px; border-bottom:1px solid {s['border']}; }}
            QTreeWidget::item:selected {{ background:{s['primary']}40; }}
            QTreeWidget::item:hover {{ background:{s['border']}; }}
            QHeaderView::section {{ background:rgba(0,0,0,0.3); color:{s['text2']}; padding:8px 6px; border:none; border-bottom:2px solid {s['primary']}; font-weight:600; font-size:10px; }}
        """)
        self.tree.itemClicked.connect(self._on_tree_click)
        ll.addWidget(self.tree)

        # RIGHT: Timeline
        rf = QFrame()
        rf.setStyleSheet(f"QFrame {{ background:{s['card_bg']}; border:1px solid {s['border']}; border-radius:8px; }}")
        rl = QVBoxLayout(rf)
        rl.setContentsMargins(12, 10, 12, 10)
        rl.setSpacing(6)

        self.tl_hdr = QLabel("Bir kayıt seçerek izlenebilirlik akışını görüntüleyin")
        self.tl_hdr.setStyleSheet(f"color:{s['muted']}; font-size:12px; padding:8px 0;")
        rl.addWidget(self.tl_hdr)

        self.sum_frame = QFrame()
        self.sum_frame.setVisible(False)
        self.sum_lo = QHBoxLayout(self.sum_frame)
        self.sum_lo.setContentsMargins(0, 0, 0, 4)
        self.sum_lo.setSpacing(6)
        rl.addWidget(self.sum_frame)

        self.mat_lo = QVBoxLayout()
        rl.addLayout(self.mat_lo)

        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setStyleSheet(f"""
            QScrollArea {{ border:none; background:transparent; }}
            QScrollBar:vertical {{ background:{s['input_bg']}; width:6px; border-radius:3px; }}
            QScrollBar::handle:vertical {{ background:{s['border']}; border-radius:3px; min-height:30px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)
        self.tl_w = QWidget()
        self.tl_w.setStyleSheet("background:transparent;")
        self.tl_lo = QVBoxLayout(self.tl_w)
        self.tl_lo.setContentsMargins(0, 0, 0, 0)
        self.tl_lo.setSpacing(4)
        self.tl_lo.setAlignment(Qt.AlignTop)
        sc.setWidget(self.tl_w)
        rl.addWidget(sc)

        sp.addWidget(lf)
        sp.addWidget(rf)
        sp.setSizes([300, 750])
        sp.setStretchFactor(0, 1)
        sp.setStretchFactor(1, 2)
        layout.addWidget(sp)

    # ═══════════════════════════════════════════════════════════
    # LOAD → TREE
    # ═══════════════════════════════════════════════════════════
    def _load_kayitlar(self):
        self.tree.clear()
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT ie.lot_no, ie.stok_kodu, ie.is_emri_no, ie.durum, 
                       ie.olusturma_tarihi, ie.id
                FROM siparis.is_emirleri ie
                WHERE ie.silindi_mi = 0 AND ie.lot_no IS NOT NULL
                ORDER BY ie.olusturma_tarihi DESC
            """)
            rows = cur.fetchall()
            conn.close()

            # Parent lot gruplama
            parent_map = {}
            for row in rows:
                parent = self._get_parent_lot(row[0])
                if parent not in parent_map:
                    parent_map[parent] = []
                parent_map[parent].append(row)

            sorted_parents = sorted(parent_map.items(),
                key=lambda x: max((r[4] for r in x[1] if r[4]), default=datetime.min),
                reverse=True)

            dc = {'TAMAMLANDI': '#10B981', 'STOKTA': '#F59E0B', 'URETIMDE': '#3B82F6', 'IPTAL': '#EF4444'}
            tot = len(sorted_parents)
            done = sum(1 for _, ch in sorted_parents if all(r[3] and 'TAMAMLAND' in r[3] for r in ch))
            self.stat_labels['toplam'].setText(f"📦 {tot}")
            self.stat_labels['ok'].setText(f"✅ {done}")
            self.stat_labels['wip'].setText(f"🔄 {tot - done}")

            for parent_lot, children in sorted_parents[:200]:
                stok = children[0][1] or '-'
                child_count = len(children)
                all_done = all(r[3] and 'TAMAMLAND' in r[3] for r in children)
                any_fail = any(r[3] and 'IPTAL' in r[3] for r in children)
                durum_text = 'TAMAMLANDI' if all_done else ('IPTAL' if any_fail else 'DEVAM')

                parent_item = QTreeWidgetItem(self.tree)
                if child_count > 1:
                    parent_item.setText(0, f"📁 {parent_lot}  ({child_count})")
                else:
                    parent_item.setText(0, f"📋 {parent_lot}")
                parent_item.setText(1, stok)
                parent_item.setText(2, durum_text)
                parent_item.setData(0, Qt.UserRole, [c[5] for c in children])
                parent_item.setData(0, Qt.UserRole + 1, parent_lot)
                parent_item.setData(0, Qt.UserRole + 2, [c[0] for c in children])

                for k, c in dc.items():
                    if k in durum_text:
                        parent_item.setForeground(2, QColor(c))
                        break
                else:
                    parent_item.setForeground(2, QColor('#3B82F6'))

                if child_count > 1:
                    for child in children:
                        lot_no = child[0]
                        suffix = lot_no.replace(parent_lot, '').lstrip('-')
                        child_item = QTreeWidgetItem(parent_item)
                        child_item.setText(0, f"  └ {suffix}" if suffix else f"  └ {lot_no}")
                        child_item.setText(1, child[1] or '-')
                        child_item.setText(2, child[3] or '-')
                        child_item.setData(0, Qt.UserRole, [child[5]])
                        child_item.setData(0, Qt.UserRole + 1, parent_lot)
                        child_item.setData(0, Qt.UserRole + 2, [child[0]])
                        for k, c in dc.items():
                            if child[3] and k in child[3]:
                                child_item.setForeground(2, QColor(c))
                                break
                        child_item.setForeground(0, QColor(self.s['text2']))

        except Exception as e:
            print(f"[İZLENEBİLİRLİK YÜKLEME HATASI] {e}")
            traceback.print_exc()

    def _search(self):
        t = self.search_input.text().strip().upper()
        if not t:
            for i in range(self.tree.topLevelItemCount()):
                self.tree.topLevelItem(i).setHidden(False)
            return
        col = {0: 0, 1: 1, 2: 0}.get(self.arama_tipi.currentIndex(), 0)
        for i in range(self.tree.topLevelItemCount()):
            item = self.tree.topLevelItem(i)
            match = t in (item.text(col) or '').upper()
            if not match:
                for j in range(item.childCount()):
                    if t in (item.child(j).text(col) or '').upper():
                        match = True
                        break
            item.setHidden(not match)

    def _on_tree_click(self, item, column):
        ie_ids = item.data(0, Qt.UserRole)
        parent_lot = item.data(0, Qt.UserRole + 1)
        lot_nos = item.data(0, Qt.UserRole + 2)
        if not ie_ids or not lot_nos:
            return

        stok = item.text(1)
        cnt = len(lot_nos)
        if cnt > 1:
            sub = f"  <span style='font-size:10px;color:{self.s['muted']};'>({stok} • {cnt} alt lot)</span>"
        else:
            sub = f"  <span style='font-size:10px;color:{self.s['muted']};'>({stok})</span>"
        self.tl_hdr.setText(f"<span style='font-size:14px;font-weight:700;color:{self.s['text']};'>{parent_lot}</span>{sub}")
        self.tl_hdr.setTextFormat(Qt.RichText)
        self._load_timeline(parent_lot, lot_nos, ie_ids)

    # ═══════════════════════════════════════════════════════════
    # 14-STEP TIMELINE
    # ═══════════════════════════════════════════════════════════
    def _lph(self, lst):
        return ','.join(['?' for _ in lst])

    def _load_timeline(self, parent_lot, lot_nos, ie_ids):
        s = self.s
        self._clear(self.tl_lo)
        self._clear(self.sum_lo)
        self._clear(self.mat_lo)
        self.sum_frame.setVisible(False)
        steps = []
        appr = []
        lph = self._lph(lot_nos)
        # parent_lot'u da dahil et (irsaliye satirlarinda ana lot kayitli)
        all_lots = list(set(lot_nos + [parent_lot]))
        alph_all = self._lph(all_lots)
        iph = self._lph(ie_ids) if ie_ids else '0'

        try:
            conn = get_db_connection()
            cur = conn.cursor()

            # ① İŞ EMRİ
            if ie_ids:
                try:
                    cur.execute(f"""SELECT ie.is_emri_no, ie.lot_no, ie.cari_unvani, ie.stok_kodu, ie.stok_adi,
                        ie.planlanan_miktar, ie.durum, ie.olusturma_tarihi, ie.termin_tarihi, p.ad+' '+p.soyad
                        FROM siparis.is_emirleri ie LEFT JOIN ik.personeller p ON ie.olusturan_id=p.id
                        WHERE ie.id IN ({iph})""", (*ie_ids,))
                    for r in cur.fetchall():
                        steps.append(('is_emri', {'status': 'completed', 'tarih': r[7],
                            'detay': [('İş Emri No', r[0]), ('Müşteri', r[2] or '-'), ('Stok', f"{r[3]} - {r[4]}"),
                                      ('Miktar', self._fmt(r[5])), ('Termin', r[8].strftime('%d.%m.%Y') if r[8] else '-'), ('Durum', r[6] or '-')],
                            'onay_bilgi': [{'role': 'Oluşturan', 'name': r[9] or '-', 'icon': '👤', 'result': ''}]}))
                        appr.append({'step': 'İş Emri', 'person': r[9] or '-', 'result': 'OLUŞTURULDU', 'tarih': r[7]})
                except Exception as e:
                    print(f"① {e}")

            # ② GİRİŞ İRSALİYE
            try:
                # lot_nos palet lot olabilir (LOT-2501-0001-01), irsaliye_satirlar'da ana lot (LOT-2501-0001) kayıtlı
                # Hem lot_nos hem parent_lot ile ara
                all_lots = list(set(lot_nos + [parent_lot]))
                alph = self._lph(all_lots)
                cur.execute(f"""SELECT gi.irsaliye_no, gi.cari_unvani, gi.cari_irsaliye_no, gi.tarih, gi.teslim_alan,
                    gi.arac_plaka, gi.sofor_adi, gi.durum, gis.miktar, gis.kaplama, gis.stok_kodu, gis.stok_adi
                    FROM siparis.giris_irsaliyeleri gi JOIN siparis.giris_irsaliye_satirlar gis ON gis.irsaliye_id=gi.id
                    WHERE gis.lot_no IN ({alph}) ORDER BY gi.tarih""", (*all_lots,))
                for r in cur.fetchall():
                    steps.append(('giris_irsaliye', {'status': 'completed', 'tarih': r[3],
                        'detay': [('İrsaliye', r[0] or '-'), ('Müşteri İrs.', r[2] or '-'), ('Müşteri', r[1] or '-'),
                                  ('Miktar', self._fmt(r[8])), ('Stok', f"{r[10] or ''} {r[11] or ''}".strip() or '-'), ('Kaplama', r[9] or '-')],
                        'onay_bilgi': [{'role': 'Teslim Alan', 'name': r[4] or '-', 'icon': '📋', 'result': ''}]}))
                    appr.append({'step': 'Giriş İrsaliye', 'person': r[4] or '-', 'result': r[7] or 'GİRİŞ', 'tarih': r[3]})
            except Exception as e:
                print(f"② {e}")

            # ③ MAL KABUL
            try:
                cur.execute(f"""SELECT mk.kabul_no, mk.tarih, mk.tedarikci_irsaliye_no, mk.durum,
                    p1.ad+' '+p1.soyad, mks.teslim_miktar, mks.kabul_miktar, mks.red_miktar,
                    mks.kalite_durumu, mks.sertifika_no, p2.ad+' '+p2.soyad, mks.kalite_kontrol_tarihi
                    FROM satinalma.mal_kabuller mk JOIN satinalma.mal_kabul_satirlari mks ON mks.kabul_id=mk.id
                    LEFT JOIN ik.personeller p1 ON mk.teslim_alan_id=p1.id
                    LEFT JOIN ik.personeller p2 ON mks.kalite_kontrol_eden_id=p2.id
                    WHERE mks.lot_no IN ({lph}) ORDER BY mk.tarih""", (*lot_nos,))
                for r in cur.fetchall():
                    st = 'completed' if r[3] == 'TAMAMLANDI' else ('failed' if r[8] == 'RED' else 'active')
                    oa = [{'role': 'Teslim Alan', 'name': r[4] or '-', 'icon': '📦', 'result': ''}]
                    if r[10]:
                        oa.append({'role': 'Kalite', 'name': r[10], 'icon': '🔬', 'result': r[8] or '-'})
                        appr.append({'step': 'Mal Kabul Kalite', 'person': r[10], 'result': r[8] or '-', 'tarih': r[11]})
                    steps.append(('mal_kabul', {'status': st, 'status_text': r[8] or r[3] or '-', 'tarih': r[1],
                        'detay': [('Kabul No', r[0] or '-'), ('Ted. İrs.', r[2] or '-'), ('Teslim', self._fmt(r[5])),
                                  ('Kabul', self._fmt(r[6])), ('Red', self._fmt(r[7])), ('Sertifika', r[9] or '-')],
                        'onay_bilgi': oa}))
                    appr.append({'step': 'Mal Kabul', 'person': r[4] or '-', 'result': r[3] or '-', 'tarih': r[1]})
            except Exception as e:
                print(f"③ {e}")

            # ④ DEPO HAREKETLERİ
            try:
                cur.execute(f"""SELECT hl.miktar, COALESCE(dh.kod,dk.kod,'-'), COALESCE(dh.ad,dk.ad,'-'),
                    hl.hareket_zamani, ht.ad, ht.yon,
                    COALESCE(dk.kod+' - '+dk.ad,'') as kaynak, COALESCE(dh.kod+' - '+dh.ad,'') as hedef
                    FROM stok.hareket_log hl JOIN tanim.hareket_tipleri ht ON hl.hareket_tipi_id=ht.id
                    LEFT JOIN tanim.depolar dh ON hl.hedef_depo_id=dh.id
                    LEFT JOIN tanim.depolar dk ON hl.kaynak_depo_id=dk.id
                    WHERE hl.lot_no IN ({lph}) AND hl.iptal_mi=0 ORDER BY hl.hareket_zamani""", (*lot_nos,))
                for r in cur.fetchall():
                    yon = {'GIRIS': 'GİRİŞ', 'CIKIS': 'ÇIKIŞ', 'TRANSFER': 'TRANSFER'}.get(r[5] or '', 'TRANSFER')
                    det = [('Miktar', self._fmt(r[0])), ('İşlem', r[4] or '-')]
                    if r[6]: det.append(('Kaynak', r[6]))
                    if r[7]: det.append(('Hedef', r[7]))
                    steps.append(('depo_hareket', {'status': 'completed', 'status_text': yon, 'tarih': r[3],
                        'detay': det}))
            except Exception as e:
                print(f"④ {e}")

            # ④b DEPO ÇIKIŞ EMİRLERİ (Depodan üretime çıkış)
            if ie_ids:
                try:
                    cur.execute(f"""SELECT e.emir_no, e.lot_no, e.stok_kodu, e.stok_adi, e.talep_miktar,
                        e.transfer_miktar, e.durum, e.olusturma_tarihi, e.tamamlanma_tarihi,
                        d.kod+' - '+d.ad as hedef_depo
                        FROM stok.depo_cikis_emirleri e
                        LEFT JOIN tanim.depolar d ON e.hedef_depo_id=d.id
                        WHERE e.is_emri_id IN ({iph}) ORDER BY e.olusturma_tarihi""", (*ie_ids,))
                    for r in cur.fetchall():
                        st = 'completed' if r[6] == 'TAMAMLANDI' else ('active' if r[6] == 'BEKLIYOR' else 'warning')
                        steps.append(('depo_hareket', {'status': st, 'status_text': f"ÇIKIŞ - {r[6] or '-'}", 'tarih': r[7],
                            'detay': [('Emir No', r[0] or '-'), ('Lot', r[1] or '-'), ('Stok', f"{r[2] or ''} {r[3] or ''}".strip() or '-'),
                                      ('Talep', self._fmt(r[4])), ('Transfer', self._fmt(r[5])), ('Hedef Depo', r[9] or '-')]}))
                except Exception as e:
                    print(f"④b {e}")

            # ⑤ GİRİŞ KALİTE (muayeneler)
            try:
                cur.execute(f"""SELECT m.tarih, m.sonuc, p.ad+' '+p.soyad, m.numune_miktari,
                    m.kabul_miktari, m.red_miktari, m.notlar
                    FROM kalite.muayeneler m LEFT JOIN ik.personeller p ON m.muayeneci_id=p.id
                    WHERE m.lot_no IN ({lph}) AND m.muayene_tipi='GIRIS' ORDER BY m.tarih""", (*lot_nos,))
                for r in cur.fetchall():
                    st = 'completed' if r[1] == 'KABUL' else ('failed' if r[1] == 'RED' else 'warning')
                    steps.append(('giris_kalite', {'status': st, 'status_text': r[1] or '-', 'tarih': r[0],
                        'detay': [('Numune', self._fmt(r[3])), ('Kabul', self._fmt(r[4])), ('Red', self._fmt(r[5])), ('Not', r[6] or '-')],
                        'onay_bilgi': [{'role': 'Muayeneci', 'name': r[2] or '-', 'icon': '🔬', 'result': r[1] or '-'}]}))
                    appr.append({'step': 'Giriş Kalite', 'person': r[2] or '-', 'result': r[1] or '-', 'tarih': r[0]})
            except Exception as e:
                print(f"⑤ {e}")

            # ⑥ PLANLAMA
            if ie_ids:
                try:
                    cur.execute(f"""SELECT p.tarih, p.durum, h.ad, p.planlanan_bara
                        FROM uretim.planlama p LEFT JOIN tanim.uretim_hatlari h ON p.hat_id=h.id
                        WHERE p.is_emri_id IN ({iph}) ORDER BY p.tarih""", (*ie_ids,))
                    for r in cur.fetchall():
                        st = 'completed' if r[1] and 'TAMAMLAND' in r[1] else ('active' if r[1] and 'DEVAM' in r[1] else 'warning')
                        steps.append(('planlama', {'status': st, 'status_text': r[1] or '-', 'tarih': r[0],
                            'detay': [('Hat', r[2] or '-'), ('Plan Bara', str(r[3]) if r[3] else '-'), ('Durum', r[1] or '-')]}))
                except Exception as e:
                    print(f"⑥ {e}")

            # ⑦ BARA TAKİP
            if ie_ids:
                try:
                    cur.execute(f"""SELECT bt.bara_no, bt.aski_miktar, bt.bara_miktar, bt.giris_zamani,
                        bt.cikis_zamani, bt.durum, h.ad
                        FROM uretim.bara_takip bt LEFT JOIN tanim.uretim_hatlari h ON bt.hat_id=h.id
                        WHERE bt.is_emri_id IN ({iph}) ORDER BY bt.giris_zamani""", (*ie_ids,))
                    bars = cur.fetchall()
                    if bars:
                        tot = len(bars)
                        ok = sum(1 for b in bars if b[5] and ('TAMAMLAND' in b[5] or 'CIKTI' in b[5].upper()))
                        steps.append(('bara_takip', {'status': 'completed' if ok == tot else 'active', 'count': tot,
                            'status_text': f"{ok}/{tot} Bara", 'tarih': bars[0][3],
                            'detay': [('Hat', bars[0][6] or '-'), ('Toplam Bara', str(tot)),
                                      ('İlk Giriş', bars[0][3].strftime('%d.%m.%Y %H:%M') if bars[0][3] else '-'),
                                      ('Son Çıkış', bars[-1][4].strftime('%d.%m.%Y %H:%M') if bars[-1][4] else '-'),
                                      ('Askı Miktar', self._fmt(bars[0][1]))]}))
                except Exception as e:
                    print(f"⑦ {e}")

            # ⑧ BANYO ANALİZ
            if ie_ids:
                try:
                    cur.execute(f"SELECT DISTINCT bt.hat_id FROM uretim.bara_takip bt WHERE bt.is_emri_id IN ({iph})", (*ie_ids,))
                    hat_ids = [r[0] for r in cur.fetchall() if r[0]]
                    if hat_ids:
                        cur.execute(f"SELECT MIN(giris_zamani), MAX(COALESCE(cikis_zamani,giris_zamani)) FROM uretim.bara_takip WHERE is_emri_id IN ({iph})", (*ie_ids,))
                        tr = cur.fetchone()
                        if tr and tr[0] and tr[1]:
                            hph = self._lph(hat_ids)
                            cur.execute(f"""SELECT ba.tarih, bd.ad, bd.kod, ba.sicaklik, ba.ph, ba.iletkenlik,
                                ba.kati_madde_yuzde, ba.pb_orani, ba.demir_ppm, p.ad+' '+p.soyad
                                FROM uretim.banyo_analiz_sonuclari ba JOIN uretim.banyo_tanimlari bd ON ba.banyo_id=bd.id
                                LEFT JOIN ik.personeller p ON ba.analist_id=p.id
                                WHERE bd.hat_id IN ({hph}) AND ba.tarih BETWEEN ? AND ? ORDER BY ba.tarih""", (*hat_ids, tr[0], tr[1]))
                            anl = cur.fetchall()
                            if anl:
                                a = anl[0]
                                steps.append(('banyo_analiz', {'status': 'completed', 'count': len(anl),
                                    'status_text': f"{len(anl)} Analiz", 'tarih': a[0],
                                    'detay': [('Banyo', f"{a[2]} - {a[1]}"), ('Sıcaklık', self._fmtd(a[3])),
                                              ('pH', self._fmtd(a[4])), ('İletkenlik', self._fmtd(a[5])),
                                              ('Katı Madde %', self._fmtd(a[6])), ('P/B Oranı', self._fmtd(a[7])),
                                              ('Demir ppm', self._fmtd(a[8]))],
                                    'onay_bilgi': [{'role': 'Analist', 'name': a[9] or '-', 'icon': '🧪', 'result': ''}]}))
                                if a[9]:
                                    appr.append({'step': 'Banyo Analiz', 'person': a[9], 'result': 'TAMAMLANDI', 'tarih': a[0]})
                except Exception as e:
                    print(f"⑧ {e}")

            # ⑨ İLK ÜRÜN (FR.75)
            try:
                cur.execute(f"""SELECT pc.kontrol_tarihi, pc.durum, p.ad+' '+p.soyad, pc.toplam_adet,
                    pc.saglam_adet, pc.hatali_adet, pc.kalinlik_olcum, pc.not_text
                    FROM kalite.proses_kontrol pc LEFT JOIN ik.personeller p ON pc.kontrol_eden_id=p.id
                    WHERE pc.lot_no IN ({lph}) ORDER BY pc.kontrol_tarihi""", (*lot_nos,))
                for r in cur.fetchall():
                    st = 'completed' if r[1] == 'TAMAMLANDI' else 'warning'
                    steps.append(('ilk_urun', {'status': st, 'status_text': r[1] or '-', 'tarih': r[0],
                        'detay': [('Toplam', self._fmt(r[3])), ('Sağlam', self._fmt(r[4])), ('Hatalı', self._fmt(r[5])),
                                  ('Kalınlık', self._fmtd(r[6], 2)), ('Not', r[7] or '-')],
                        'onay_bilgi': [{'role': 'Kontrol Eden', 'name': r[2] or '-', 'icon': '🔧', 'result': r[1] or '-'}]}))
                    appr.append({'step': 'İlk Ürün', 'person': r[2] or '-', 'result': r[1] or '-', 'tarih': r[0]})
            except Exception as e:
                print(f"⑨ {e}")

            # ⑩ SÖKÜM
            try:
                cur.execute(f"""SELECT si.is_emri_no, si.sokum_tipi, si.miktar, si.baslangic_tarihi, si.durum,
                    sg.giris_miktar, sg.kalan_miktar, sg.kalite_durumu, sg.sokum_suresi,
                    p1.ad+' '+p1.soyad, p2.ad+' '+p2.soyad
                    FROM uretim.sokum_is_emirleri si
                    LEFT JOIN uretim.sokum_giris sg ON sg.sokum_is_emri_id=si.id
                    LEFT JOIN ik.personeller p1 ON si.sorumlu_id=p1.id
                    LEFT JOIN ik.personeller p2 ON sg.giris_yapan_id=p2.id
                    WHERE si.lot_no IN ({lph}) ORDER BY si.baslangic_tarihi""", (*lot_nos,))
                for r in cur.fetchall():
                    st = 'completed' if r[4] and 'TAMAMLAND' in r[4] else 'active'
                    oa = [{'role': 'Sorumlu', 'name': r[9] or '-', 'icon': '🏭', 'result': ''}]
                    if r[10]:
                        oa.append({'role': 'Giriş Yapan', 'name': r[10], 'icon': '👤', 'result': r[7] or '-'})
                    steps.append(('sokum', {'status': st, 'status_text': r[4] or '-', 'tarih': r[3],
                        'detay': [('Söküm Tipi', r[1] or '-'), ('Miktar', self._fmt(r[2])), ('Giriş', self._fmt(r[5])),
                                  ('Kalan', self._fmt(r[6])), ('Süre (dk)', str(r[8]) if r[8] else '-'), ('Kalite', r[7] or '-')],
                        'onay_bilgi': oa}))
                    if r[9]:
                        appr.append({'step': 'Söküm', 'person': r[9] or '-', 'result': r[4] or '-', 'tarih': r[3]})
            except Exception as e:
                print(f"⑩ {e}")

            # ⑪ FİNAL KONTROL
            try:
                cur.execute(f"""SELECT fc.kontrol_tarihi, fc.sonuc, fc.kontrol_miktar, fc.saglam_adet,
                    fc.hatali_adet, fc.aciklama, p.ad+' '+p.soyad, fc.id
                    FROM kalite.final_kontrol fc LEFT JOIN ik.personeller p ON fc.kontrol_eden_id=p.id
                    WHERE fc.lot_no IN ({lph}) ORDER BY fc.kontrol_tarihi""", (*lot_nos,))
                for r in cur.fetchall():
                    st = 'completed' if r[1] == 'KABUL' else ('warning' if r[1] == 'KISMI' else 'failed')
                    ht = ''
                    try:
                        cur.execute("SELECT ht.ad, fh.adet FROM kalite.final_kontrol_hatalar fh LEFT JOIN tanim.hata_turleri ht ON fh.hata_turu_id=ht.id WHERE fh.final_kontrol_id=?", (r[7],))
                        hts = cur.fetchall()
                        if hts:
                            ht = ', '.join([f"{h[0]}({h[1]})" for h in hts])
                    except Exception:
                        pass
                    det = [('Kontrol', self._fmt(r[2])), ('Sağlam', self._fmt(r[3])), ('Hatalı', self._fmt(r[4])), ('Sonuç', r[1] or '-')]
                    if ht:
                        det.append(('Hatalar', ht))
                    if r[5]:
                        det.append(('Açıklama', r[5]))
                    steps.append(('final_kontrol', {'status': st, 'status_text': r[1] or '-', 'tarih': r[0],
                        'detay': det, 'onay_bilgi': [{'role': 'Kontrol Eden', 'name': r[6] or '-', 'icon': '✅', 'result': r[1] or '-'}]}))
                    appr.append({'step': 'Final Kontrol', 'person': r[6] or '-', 'result': r[1] or '-', 'tarih': r[0]})
            except Exception as e:
                print(f"⑪ {e}")

            # ⑫ RED / UYGUNSUZLUK
            try:
                cur.execute(f"""SELECT ur.red_tarihi, ur.red_miktar, ur.durum, ur.islem_tipi, ur.aciklama,
                    ur.karar, p1.ad+' '+p1.soyad, p2.ad+' '+p2.soyad, ur.karar_tarihi, ht.ad
                    FROM kalite.uretim_redler ur LEFT JOIN ik.personeller p1 ON ur.kontrol_eden_id=p1.id
                    LEFT JOIN ik.personeller p2 ON ur.karar_veren_id=p2.id
                    LEFT JOIN tanim.hata_turleri ht ON ur.hata_turu_id=ht.id
                    WHERE ur.lot_no IN ({lph}) ORDER BY ur.red_tarihi""", (*lot_nos,))
                for r in cur.fetchall():
                    oa = [{'role': 'Tespit Eden', 'name': r[6] or '-', 'icon': '⚠️', 'result': r[2] or '-'}]
                    if r[7]:
                        oa.append({'role': 'Karar Veren', 'name': r[7], 'icon': '👔', 'result': r[5] or '-'})
                        appr.append({'step': 'Red Karar', 'person': r[7], 'result': r[5] or '-', 'tarih': r[8]})
                    steps.append(('red_uygunsuzluk', {'status': 'failed', 'status_text': r[5] or r[2] or 'RED', 'tarih': r[0],
                        'detay': [('Red Miktar', self._fmt(r[1])), ('İşlem', r[3] or '-'), ('Hata', r[9] or '-'),
                                  ('Karar', r[5] or '-'), ('Açıklama', r[4] or '-')],
                        'onay_bilgi': oa}))
                    appr.append({'step': 'Üretim Red', 'person': r[6] or '-', 'result': r[2] or '-', 'tarih': r[0]})
            except Exception as e:
                print(f"⑫a {e}")

            try:
                cur.execute(f"""SELECT rk.karar_zamani, rk.karar, rk.miktar, rk.aciklama,
                    p.ad+' '+p.soyad, ht.ad, d.ad
                    FROM kalite.red_karar rk LEFT JOIN ik.personeller p ON rk.kararci_id=p.id
                    LEFT JOIN tanim.hata_turleri ht ON rk.hata_turu_id=ht.id
                    LEFT JOIN tanim.depolar d ON rk.hedef_depo_id=d.id
                    WHERE rk.lot_no IN ({lph}) ORDER BY rk.karar_zamani""", (*lot_nos,))
                for r in cur.fetchall():
                    steps.append(('red_uygunsuzluk', {'status': 'warning', 'status_text': r[1] or '-', 'tarih': r[0],
                        'detay': [('Karar', r[1] or '-'), ('Miktar', self._fmt(r[2])), ('Hata', r[5] or '-'),
                                  ('Hedef Depo', r[6] or '-'), ('Açıklama', r[3] or '-')],
                        'onay_bilgi': [{'role': 'Karar Veren', 'name': r[4] or '-', 'icon': '👔', 'result': r[1] or '-'}]}))
                    appr.append({'step': 'Red Karar', 'person': r[4] or '-', 'result': r[1] or '-', 'tarih': r[0]})
            except Exception as e:
                print(f"⑫b {e}")

            try:
                cur.execute(f"""SELECT u.kayit_no, u.kayit_tipi, u.kayit_tarihi, u.hata_tanimi, u.tespit_yeri,
                    u.oncelik, u.durum, u.etkilenen_miktar, p1.ad+' '+p1.soyad, p2.ad+' '+p2.soyad
                    FROM kalite.uygunsuzluklar u LEFT JOIN ik.personeller p1 ON u.bildiren_id=p1.id
                    LEFT JOIN ik.personeller p2 ON u.sorumlu_id=p2.id
                    WHERE u.lot_no IN ({lph}) AND (u.kayit_tipi IS NULL OR u.kayit_tipi!='MUSTERI_SIKAYETI')
                    ORDER BY u.kayit_tarihi""", (*lot_nos,))
                for r in cur.fetchall():
                    st = 'completed' if r[6] == 'KAPALI' else ('failed' if r[6] == 'ACIK' else 'warning')
                    steps.append(('red_uygunsuzluk', {'status': st, 'status_text': r[6] or '-', 'tarih': r[2],
                        'detay': [('Kayıt No', r[0] or '-'), ('Tip', r[1] or '-'), ('Hata', r[3] or '-'),
                                  ('Tespit', r[4] or '-'), ('Etkilenen', self._fmt(r[7])), ('Öncelik', r[5] or '-')],
                        'onay_bilgi': [{'role': 'Bildiren', 'name': r[8] or '-', 'icon': '📢', 'result': ''},
                                       {'role': 'Sorumlu', 'name': r[9] or '-', 'icon': '👔', 'result': r[6] or '-'}]}))
                    appr.append({'step': 'Uygunsuzluk', 'person': r[9] or '-', 'result': r[6] or '-', 'tarih': r[2]})
            except Exception as e:
                print(f"⑫c {e}")

            # ⑬ SEVKİYAT & ÇIKIŞ İRSALİYE
            try:
                # Çıkış irsaliyeleri - lot_no veya is_emri_id ile ara
                if ie_ids:
                    cur.execute(f"""SELECT DISTINCT ci.irsaliye_no, ci.tarih, ci.arac_plaka, ci.sofor_adi, ci.durum,
                        cs.miktar, c.unvan, ci.tasiyici_firma, cs.lot_no
                        FROM siparis.cikis_irsaliyeleri ci
                        JOIN siparis.cikis_irsaliye_satirlar cs ON cs.irsaliye_id=ci.id
                        LEFT JOIN musteri.cariler c ON ci.cari_id=c.id
                        WHERE (cs.lot_no IN ({lph}) OR cs.is_emri_id IN ({iph}))
                          AND (ci.silindi_mi=0 OR ci.silindi_mi IS NULL)
                        ORDER BY ci.tarih""", (*lot_nos, *ie_ids))
                else:
                    cur.execute(f"""SELECT DISTINCT ci.irsaliye_no, ci.tarih, ci.arac_plaka, ci.sofor_adi, ci.durum,
                        cs.miktar, c.unvan, ci.tasiyici_firma, cs.lot_no
                        FROM siparis.cikis_irsaliyeleri ci
                        JOIN siparis.cikis_irsaliye_satirlar cs ON cs.irsaliye_id=ci.id
                        LEFT JOIN musteri.cariler c ON ci.cari_id=c.id
                        WHERE cs.lot_no IN ({lph})
                          AND (ci.silindi_mi=0 OR ci.silindi_mi IS NULL)
                        ORDER BY ci.tarih""", (*lot_nos,))
                for r in cur.fetchall():
                    st_map = {'HAZIRLANDI': 'active', 'SEVK_EDILDI': 'completed', 'TESLIM_EDILDI': 'completed', 'IPTAL': 'failed'}
                    st = st_map.get(r[4], 'warning')
                    steps.append(('sevkiyat', {'status': st, 'status_text': r[4] or '-', 'tarih': r[1],
                        'detay': [('İrsaliye No', r[0] or '-'), ('Müşteri', r[6] or '-'), ('Miktar', self._fmt(r[5])),
                                  ('Plaka', r[2] or '-'), ('Şoför', r[3] or '-'), ('Taşıyıcı', r[7] or '-')],
                        'onay_bilgi': []}))
                    appr.append({'step': 'Çıkış İrsaliye', 'person': r[3] or '-', 'result': r[4] or '-', 'tarih': r[1]})
            except Exception as e:
                print(f"⑬ {e}")

            # ⑭ MÜŞTERİ ŞİKAYETİ
            try:
                cur.execute(f"""SELECT u.kayit_no, u.kayit_tarihi, u.hata_tanimi, u.durum, p.ad+' '+p.soyad, c.unvan
                    FROM kalite.uygunsuzluklar u LEFT JOIN ik.personeller p ON u.sorumlu_id=p.id
                    LEFT JOIN musteri.cariler c ON u.cari_id=c.id
                    WHERE u.lot_no IN ({lph}) AND u.kayit_tipi='MUSTERI_SIKAYETI' ORDER BY u.kayit_tarihi""", (*lot_nos,))
                for r in cur.fetchall():
                    st = 'failed' if r[3] == 'ACIK' else ('completed' if r[3] == 'KAPALI' else 'warning')
                    steps.append(('musteri_sikayet', {'status': st, 'status_text': r[3] or '-', 'tarih': r[1],
                        'detay': [('Kayıt No', r[0] or '-'), ('Müşteri', r[5] or '-'), ('Şikayet', r[2] or '-')],
                        'onay_bilgi': [{'role': 'Sorumlu', 'name': r[4] or '-', 'icon': '📞', 'result': r[3] or '-'}]}))
                    appr.append({'step': 'Müşteri Şikayeti', 'person': r[4] or '-', 'result': r[3] or '-', 'tarih': r[1]})
            except Exception as e:
                print(f"⑭ {e}")

            # Lot Durum Geçmişi
            try:
                cur.execute(f"""SELECT ldg.eski_durum, ldg.yeni_durum, ldg.degisim_zamani, p.ad+' '+p.soyad
                    FROM stok.lot_durum_gecmisi ldg LEFT JOIN ik.personeller p ON ldg.degistiren_id=p.id
                    WHERE ldg.lot_no IN ({lph}) ORDER BY ldg.degisim_zamani""", (*lot_nos,))
                for r in cur.fetchall():
                    appr.append({'step': f"{r[0] or '?'}→{r[1] or '?'}", 'person': r[3] or '-', 'result': r[1] or '-', 'tarih': r[2]})
            except Exception as e:
                print(f"Lot geçmişi: {e}")

            conn.close()
        except Exception as e:
            print(f"[TIMELINE HATASI] {e}")
            traceback.print_exc()

        # Sort by date (normalize date vs datetime)
        def _to_dt(v):
            if v is None: return datetime.min
            if isinstance(v, datetime): return v
            if isinstance(v, date): return datetime(v.year, v.month, v.day)
            return datetime.min
        steps.sort(key=lambda x: _to_dt(x[1].get('tarih')))

        if steps:
            self._build_summary(steps)
        if appr:
            appr.sort(key=lambda a: _to_dt(a.get('tarih')))
            self.mat_lo.addWidget(ApprovalMatrixWidget(appr, s))

        if not steps:
            el = QLabel("ℹ️  Bu lot için henüz izlenebilirlik verisi bulunamadı")
            el.setStyleSheet(f"color:{s['muted']}; font-size:12px; padding:40px 20px;")
            el.setAlignment(Qt.AlignCenter)
            self.tl_lo.addWidget(el)
        else:
            for idx, (sk_, data) in enumerate(steps):
                last = idx == len(steps) - 1
                rw = QWidget()
                rw.setStyleSheet("background:transparent;")
                rl = QHBoxLayout(rw)
                rl.setContentsMargins(0, 0, 0, 0)
                rl.setSpacing(0)
                st = data.get('status', 'pending')
                cm = ST_CLR(s)
                rl.addWidget(TimelineConnector(cm.get(st, s['muted']), last), 0, Qt.AlignTop)
                rl.addWidget(TimelineStepWidget(sk_, data, s), 1)
                self.tl_lo.addWidget(rw)
        self.tl_lo.addStretch()
        # ScrollArea'nın içeriği güncellemesi için
        self.tl_w.adjustSize()
        self.tl_w.updateGeometry()

    def _build_summary(self, steps):
        s = self.s
        self._clear(self.sum_lo)
        ok = sum(1 for _, d in steps if d.get('status') == 'completed')
        wrn = sum(1 for _, d in steps if d.get('status') in ('warning', 'active'))
        fail = sum(1 for _, d in steps if d.get('status') == 'failed')
        tot = len(steps)
        types = len(set(k for k, _ in steps))
        sums = [(f"{tot}", "Toplam", s['text2'], s['border']),
                (f"{types}", "Adım", s['info'], s['info']),
                (f"{ok}", "Tamam", s['ok'], s['ok'])]
        if wrn:
            sums.append((f"{wrn}", "Devam", s['warn'], s['warn']))
        if fail:
            sums.append((f"{fail}", "Red", s['err'], s['err']))
        for v, l, c, bc in sums:
            f = QFrame()
            f.setStyleSheet(f"QFrame {{ background:{bc}11; border:1px solid {bc}33; border-radius:6px; padding:6px 14px; }}")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(0, 0, 0, 0)
            fl.setSpacing(0)
            vl = QLabel(v)
            vl.setStyleSheet(f"color:{c}; font-size:18px; font-weight:700; background:transparent; border:none;")
            vl.setAlignment(Qt.AlignCenter)
            fl.addWidget(vl)
            dl = QLabel(l)
            dl.setStyleSheet(f"color:{s['muted']}; font-size:9px; background:transparent; border:none;")
            dl.setAlignment(Qt.AlignCenter)
            fl.addWidget(dl)
            self.sum_lo.addWidget(f)
        self.sum_lo.addStretch()
        self.sum_frame.setVisible(True)
