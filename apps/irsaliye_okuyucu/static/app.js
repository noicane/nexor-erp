// NEXOR Irsaliye Okuyucu - Frontend
// Basit state makinesi: capture -> loading -> review -> success

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const STATE = {
  imageFile: null,
  parseResult: null,
};

// ============ UI STATE MAKINESI ============
function goStep(name) {
  $$('.step').forEach(s => s.classList.remove('active'));
  $(`#step-${name}`).classList.add('active');
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function toast(msg, type = '') {
  const t = $('#toast');
  t.textContent = msg;
  t.className = 'toast show ' + type;
  setTimeout(() => { t.classList.remove('show'); }, 3500);
}

// ============ HEALTH ============
async function healthCheck() {
  const badge = $('#status-badge');
  try {
    const r = await fetch('/api/health');
    const d = await r.json();
    if (d.status === 'ok') {
      badge.textContent = `· ${d.stok_cache} stok · hazır`;
      badge.dataset.status = 'ok';
    } else {
      const eksik = [];
      if (!d.anthropic_api_key) eksik.push('API key');
      if (!d.db) eksik.push('DB');
      badge.textContent = `· eksik: ${eksik.join(', ')}`;
      badge.dataset.status = 'degraded';
    }
  } catch (e) {
    badge.textContent = '· sunucu hatası';
    badge.dataset.status = 'error';
  }
}

// ============ FOTO SEC / CEK ============
$('#foto-input').addEventListener('change', (e) => {
  const f = e.target.files[0];
  if (!f) return;
  STATE.imageFile = f;

  const reader = new FileReader();
  reader.onload = (ev) => {
    $('#preview-img').src = ev.target.result;
    $('#preview-wrap').classList.add('has-image');
    $('#btn-oku').disabled = false;
    $('#foto-btn').textContent = '🔄 Başka Fotoğraf';
  };
  reader.readAsDataURL(f);
});

// ============ OKU (Claude Vision) ============
$('#btn-oku').addEventListener('click', async () => {
  if (!STATE.imageFile) return;
  goStep('loading');

  const fd = new FormData();
  fd.append('foto', STATE.imageFile);

  try {
    const r = await fetch('/api/parse-irsaliye', { method: 'POST', body: fd });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(err.detail || 'Parse hatası');
    }
    STATE.parseResult = await r.json();
    formDoldur(STATE.parseResult);
    goStep('review');
  } catch (e) {
    toast('Okuma hatası: ' + e.message, 'error');
    goStep('capture');
  }
});

// ============ FORM DOLDUR ============
function formDoldur(d) {
  // Cari select
  const sel = $('#cari-select');
  sel.innerHTML = '';

  if (d.cari_onerileri && d.cari_onerileri.length) {
    d.cari_onerileri.forEach((c, idx) => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = `${c.unvan} ${c.vergi_no ? '(VKN: ' + c.vergi_no + ')' : ''} · %${c.skor.toFixed(0)}`;
      if (c.id === d.secilen_cari_id) opt.selected = true;
      sel.appendChild(opt);
    });
  }
  // "Yeni cari" seçeneği
  const yeniOpt = document.createElement('option');
  yeniOpt.value = '__yeni__';
  yeniOpt.textContent = '✍️ Cari listede yok / manuel gir...';
  sel.appendChild(yeniOpt);

  // Cariye göre VKN ve manuel unvan göster/gizle
  const cariUnvanManual = $('#cari-unvan-manual');
  const cariVkn = $('#cari-vkn');

  function cariDegisti() {
    if (sel.value === '__yeni__') {
      cariUnvanManual.style.display = 'block';
      cariUnvanManual.value = d.tedarikci_unvan || '';
      cariVkn.value = d.tedarikci_vkn || '';
    } else {
      cariUnvanManual.style.display = 'none';
      const c = (d.cari_onerileri || []).find(x => x.id == sel.value);
      cariVkn.value = c?.vergi_no || d.tedarikci_vkn || '';
    }
  }
  sel.onchange = cariDegisti;

  if (!d.cari_onerileri || d.cari_onerileri.length === 0) {
    sel.value = '__yeni__';
  }
  cariDegisti();

  // Diğer alanlar
  $('#cari-irsaliye-no').value = d.cari_irsaliye_no || '';
  $('#tarih').value = d.tarih || new Date().toISOString().slice(0, 10);
  $('#arac-plaka').value = d.arac_plaka || '';
  $('#sofor-adi').value = d.sofor_adi || '';
  $('#teslim-alan').value = '';
  $('#notlar').value = d.notlar || '';

  // Kalemler
  const list = $('#kalem-liste');
  list.innerHTML = '';
  (d.kalemler || []).forEach((k, idx) => kalemEkle(k, idx + 1));
  $('#kalem-count').textContent = (d.kalemler || []).length;
}

// ============ KALEM ============
function kalemEkle(k, sira) {
  const tpl = $('#kalem-template');
  const el = tpl.content.firstElementChild.cloneNode(true);
  el.querySelector('.kalem-sira').textContent = `Kalem ${sira}`;
  el.querySelector('.k-kod').value = k?.kod || '';
  el.querySelector('.k-ad').value = k?.ad || '';
  el.querySelector('.k-miktar').value = k?.miktar || '';
  el.querySelector('.k-birim').value = k?.birim || 'ADET';
  el.querySelector('.k-kaplama').value = k?.kaplama || '';

  // Musteri kodunu ayri tut - aslında fotodan okunan
  el.dataset.musteriKodu = k?.kod || '';
  el.dataset.musteriAdi = k?.ad || '';

  // Stok öneri dropdown
  if (k?.oneriler && k.oneriler.length) {
    const oneriSel = el.querySelector('.k-oneri');
    oneriSel.innerHTML = '';
    k.oneriler.forEach((o) => {
      const opt = document.createElement('option');
      opt.value = o.urun_id;
      opt.dataset.urunKodu = o.urun_kodu;
      opt.dataset.urunAdi = o.urun_adi;
      const kaynakPrefix = o.kaynak === 'musteri_parca_no' ? '⭐ Müşteri kartından · '
                        : o.kaynak === 'musteri_parca_no_fuzzy' ? '⭐ Müşteri kartı (yakın) · '
                        : o.kaynak === 'ogrenilmis' ? '🎯 ÖĞRENİLMİŞ · '
                        : o.kaynak === 'kod_exact' ? '✅ Kod eşleşti · '
                        : '';
      opt.textContent = `${kaynakPrefix}${o.urun_kodu} · ${o.urun_adi.substring(0, 50)} · %${o.skor.toFixed(0)}`;
      if (o.urun_id === k.secilen_urun_id) opt.selected = true;
      oneriSel.appendChild(opt);
    });
    const yoksaOpt = document.createElement('option');
    yoksaOpt.value = '';
    yoksaOpt.textContent = '➖ Eşleşme yok / müşteri kodunu kullan';
    oneriSel.appendChild(yoksaOpt);
    if (!k.secilen_urun_id) oneriSel.value = '';
    el.querySelector('.k-oneri-wrap').style.display = 'block';

    // Dropdown degisince ust alanlari (stok_kodu + ad) guncelle
    const kodInput = el.querySelector('.k-kod');
    const adInput = el.querySelector('.k-ad');
    oneriSel.addEventListener('change', () => {
      const opt = oneriSel.options[oneriSel.selectedIndex];
      if (opt && opt.value && opt.dataset.urunKodu) {
        kodInput.value = opt.dataset.urunKodu;
        adInput.value = opt.dataset.urunAdi;
      } else {
        kodInput.value = el.dataset.musteriKodu;
        adInput.value = el.dataset.musteriAdi;
      }
    });
    // Baslangicta zaten secili bir eslesme varsa hemen uygula
    if (k.secilen_urun_id) {
      const sel = oneriSel.options[oneriSel.selectedIndex];
      if (sel && sel.dataset.urunKodu) {
        el.querySelector('.k-kod').value = sel.dataset.urunKodu;
        el.querySelector('.k-ad').value = sel.dataset.urunAdi;
      }
    }
  } else {
    // Hic oneri yoksa da arama butonu aktif olsun
    el.querySelector('.k-oneri-wrap').style.display = 'block';
    el.querySelector('.k-oneri').style.display = 'none';
  }

  // Arama butonu
  el.querySelector('.k-ara-btn').addEventListener('click', () => {
    openAramaModal(el, k?.ad || '');
  });

  // Sil butonu + listeye ekle (orijinal kalemEkle sonu)
  el.querySelector('.kalem-remove').addEventListener('click', () => {
    el.remove();
    guncelleKalemNumaralari();
  });
  $('#kalem-liste').appendChild(el);
}

// ============ STOK ARAMA MODALI ============
let _aktifAramaEl = null;
let _aramaTimer = null;

function openAramaModal(kalemEl, onIceriği) {
  _aktifAramaEl = kalemEl;
  const modal = $('#ara-modal');
  const input = $('#ara-input');
  const sonuclar = $('#ara-sonuclar');
  input.value = onIceriği || '';
  sonuclar.innerHTML = '';
  modal.style.display = 'flex';
  setTimeout(() => input.focus(), 50);
  if (input.value.length >= 2) aramaYap(input.value);
}

async function aramaYap(q) {
  const sonuclar = $('#ara-sonuclar');
  sonuclar.innerHTML = '<div style="padding:12px; color:var(--muted);">Aranıyor...</div>';

  // Aktif kalemin bagli oldugu carinin id'sini bul
  const cariSel = $('#cari-select');
  let cariId = cariSel.value;
  if (cariId === '__yeni__') cariId = '';

  try {
    const url = `/api/stok-ara?q=${encodeURIComponent(q)}${cariId ? '&cari_id=' + cariId : ''}&limit=15`;
    const r = await fetch(url);
    const d = await r.json();
    if (!d.sonuclar || d.sonuclar.length === 0) {
      sonuclar.innerHTML = '<div style="padding:12px; color:var(--muted);">Eşleşme bulunamadı. Daha farklı bir kelime dene.</div>';
      return;
    }
    sonuclar.innerHTML = '';
    d.sonuclar.forEach((o) => {
      const item = document.createElement('div');
      item.className = 'ara-item';
      item.innerHTML = `
        <div><span class="ara-kod">${o.urun_kodu}</span>${o.cari_oncelik ? '<span class="ara-badge">Bu müşteri</span>' : ''} <span style="color:var(--muted);font-size:11px;">·%${o.skor.toFixed(0)}</span></div>
        <div class="ara-ad">${o.urun_adi}</div>
      `;
      item.addEventListener('click', () => {
        if (_aktifAramaEl) {
          _aktifAramaEl.querySelector('.k-kod').value = o.urun_kodu;
          _aktifAramaEl.querySelector('.k-ad').value = o.urun_adi;
          // Oneri dropdown'ina da ekle ve sec
          const sel = _aktifAramaEl.querySelector('.k-oneri');
          sel.style.display = '';
          let opt = Array.from(sel.options).find(x => x.value == o.urun_id);
          if (!opt) {
            opt = document.createElement('option');
            opt.value = o.urun_id;
            opt.dataset.urunKodu = o.urun_kodu;
            opt.dataset.urunAdi = o.urun_adi;
            opt.textContent = `🔎 Aranan · ${o.urun_kodu} · ${o.urun_adi.substring(0, 40)}`;
            sel.insertBefore(opt, sel.firstChild);
          }
          sel.value = o.urun_id;
        }
        closeAramaModal();
      });
      sonuclar.appendChild(item);
    });
  } catch (e) {
    sonuclar.innerHTML = '<div style="padding:12px; color:var(--danger);">Arama hatası: ' + e.message + '</div>';
  }
}

function closeAramaModal() {
  $('#ara-modal').style.display = 'none';
  _aktifAramaEl = null;
}

document.getElementById('ara-kapat').addEventListener('click', closeAramaModal);
document.getElementById('ara-input').addEventListener('input', (e) => {
  clearTimeout(_aramaTimer);
  const q = e.target.value.trim();
  if (q.length < 2) {
    $('#ara-sonuclar').innerHTML = '<div style="padding:12px; color:var(--muted);">En az 2 harf yazın...</div>';
    return;
  }
  _aramaTimer = setTimeout(() => aramaYap(q), 250);
});
document.getElementById('ara-modal').addEventListener('click', (e) => {
  if (e.target.id === 'ara-modal') closeAramaModal();
});

function guncelleKalemNumaralari() {
  $$('.kalem-row').forEach((row, idx) => {
    row.querySelector('.kalem-sira').textContent = `Kalem ${idx + 1}`;
  });
  $('#kalem-count').textContent = $$('.kalem-row').length;
}

$('#btn-kalem-ekle').addEventListener('click', () => {
  kalemEkle({ miktar: 0 }, $$('.kalem-row').length + 1);
  $('#kalem-count').textContent = $$('.kalem-row').length;
});

// ============ KAYDET ============
$('#btn-kaydet').addEventListener('click', async () => {
  const sel = $('#cari-select');
  const secilenCariId = sel.value === '__yeni__' ? null : parseInt(sel.value);
  const cariUnvan = sel.value === '__yeni__'
    ? $('#cari-unvan-manual').value.trim()
    : (sel.options[sel.selectedIndex]?.textContent.split(' · ')[0].replace(/\(VKN:.*\)/, '').trim());

  if (!cariUnvan) {
    toast('Müşteri ünvanı zorunlu', 'error');
    return;
  }

  const kalemler = [];
  $$('.kalem-row').forEach((row, idx) => {
    const ad = row.querySelector('.k-ad').value.trim();
    const miktar = parseFloat(row.querySelector('.k-miktar').value);
    if (!ad || !miktar || miktar <= 0) return;
    const oneriSel = row.querySelector('.k-oneri');
    const secilenUrunId = oneriSel && oneriSel.value ? parseInt(oneriSel.value) : null;
    kalemler.push({
      sira: idx + 1,
      kod: row.querySelector('.k-kod').value.trim(),
      ad,
      miktar,
      birim: row.querySelector('.k-birim').value.trim() || 'ADET',
      kaplama: row.querySelector('.k-kaplama').value.trim() || null,
      secilen_urun_id: secilenUrunId,
      oneriler: [],
    });
  });

  if (kalemler.length === 0) {
    toast('En az 1 kalem zorunlu', 'error');
    return;
  }

  const tarih = $('#tarih').value;
  if (!tarih) {
    toast('Tarih zorunlu', 'error');
    return;
  }

  const body = {
    secilen_cari_id: secilenCariId,
    cari_unvan: cariUnvan,
    cari_irsaliye_no: $('#cari-irsaliye-no').value.trim(),
    tarih,
    arac_plaka: $('#arac-plaka').value.trim() || null,
    sofor_adi: $('#sofor-adi').value.trim() || null,
    teslim_alan: $('#teslim-alan').value.trim() || null,
    notlar: $('#notlar').value.trim() || null,
    kalemler,
  };

  const btn = $('#btn-kaydet');
  btn.disabled = true;
  btn.textContent = '💾 Kaydediliyor...';

  try {
    const r = await fetch('/api/kaydet', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    if (!r.ok) {
      const err = await r.json().catch(() => ({ detail: r.statusText }));
      throw new Error(err.detail || 'Kaydet hatası');
    }
    const d = await r.json();
    $('#basarili-no').textContent = d.irsaliye_no;
    $('#basarili-mesaj').textContent = d.mesaj;
    goStep('success');
  } catch (e) {
    toast('Kayıt hatası: ' + e.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '💾 NEXOR\'a Kaydet';
  }
});

// ============ NAVIGASYON ============
$('#btn-geri').addEventListener('click', () => goStep('capture'));
$('#btn-yeni').addEventListener('click', () => {
  STATE.imageFile = null;
  STATE.parseResult = null;
  $('#foto-input').value = '';
  $('#preview-wrap').classList.remove('has-image');
  $('#btn-oku').disabled = true;
  $('#foto-btn').textContent = '📸 Fotoğraf Çek';
  goStep('capture');
});

// ============ INIT ============
healthCheck();
setInterval(healthCheck, 30000);
