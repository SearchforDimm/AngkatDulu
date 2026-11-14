"""Tahap 5: kalibrasi dan evaluasi aturan peringatan AngkatDulu.

python pipeline/evaluasi/kalibrasi.py [DATA_DIR] [--keluar data/evaluasi] [--aturan config/aturan.yaml]

Fitur, status, dan kebijakan pesan diambil dari paket `mesin/` (kode yang sama dengan mesin replay),
jadi angka evaluasi di sini = perilaku mesin.

Waktu keputusan tau = akhir slot t (t + 30 menit). Fitur hanya memakai slot <= t (lihat mesin/fitur.py).
Kebenaran (IMERG, hanya untuk evaluasi, tidak pernah untuk keputusan):
  P-3J: ada slot >= 1 mm/jam di [tau, tau + 3 jam)      -> dinilai tiap slot siang (tau 06.00–17.59 WIB)
  E-3J: awal hujan siang tertangkap bila ada notifikasi BERPOTENSI TERKIRIM di [awal - 3 jam, awal]
Status BERPOTENSI: menyala saat syarat Level 2 terpenuhi; padam bila syarat hilang 60 menit atau data putus
2 jam. Notifikasi BERPOTENSI dan AMAN_LAGI: 06.00–18.00 WIB, maksimal 2 per hari per chat (proposal).
Skema uji: (1) uji silang per stasiun (atur di 3 stasiun, uji di stasiun ke-4); (2) atur Sep, uji Okt.
Keluarga aturan (anomali atau persentil) dipilih dari HSS uji silang; parameternya dari HSS di semua data.
Keduanya memakai aturan seri yang sama: HSS dibulatkan 2 desimal, lalu E-3J terbanyak. Hasil -> config/aturan.yaml.
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))
from mesin.aturan import Aturan, PenilaiAturan  # noqa: E402
from mesin.fitur import hitung_fitur, seri_layak  # noqa: E402
from mesin.kebijakan import KuotaMemori, transisi  # noqa: E402

STASIUN = ['CKRG', 'BAKO', 'CLBG', 'CJUR']
RESET = {'CJUR': pd.Timestamp('2026-09-24', tz='UTC')}    # ganti antena DOY 267 -> pembanding dimulai ulang
GRID_MULAI = pd.Timestamp('2026-09-01 00:00', tz='UTC')
GRID_AKHIR = pd.Timestamp('2026-11-01 23:30', tz='UTC')
BASAH = 1.0
WIB = pd.Timedelta(hours=7)
SETENGAH = pd.Timedelta(minutes=30)


def aturan_uji(jenis, x, d, W):
    return Aturan(nama=f'{jenis}-{x}-{d}', versi='grid', jenis=jenis, l2_min=x, l2_delta=d, jendela_hari=W,
                  reset=dict(RESET))


# ---------------------------------------------------------------- fitur + kebenaran
def fitur_stasiun(data, kode, W):
    p = pd.read_csv(Path(data) / f'pwv_30menit_{kode.lower()}.csv', parse_dates=['waktu_utc'])
    v = seri_layak(p, mulai=GRID_MULAI, akhir=GRID_AKHIR)
    f = hitung_fitur(v, W, 3, awal_seri=GRID_MULAI, reset=RESET.get(kode))
    grid = f.index
    h = pd.read_csv(Path(data) / 'hujan_30menit.csv', parse_dates=['waktu_utc'])
    r = h[h.kode_stasiun == kode].set_index('waktu_utc').hujan_mm_per_jam.reindex(grid)
    basah = (r >= BASAH).astype(float).where(r.notna())
    fut = pd.concat([basah.shift(-k) for k in range(1, 7)], axis=1).max(axis=1, skipna=True)
    f['kode_stasiun'] = kode; f['hujan_mm_per_jam'] = r; f['hujan_3j_depan'] = fut
    tau = grid + SETENGAH + WIB
    f['jam_wib'] = tau.hour
    f['siang'] = (tau.hour >= 6) & (tau.hour < 18)
    f['tanggal_wib'] = (tau - SETENGAH).normalize().tz_localize(None)
    f['bulan'] = (grid + WIB).month
    f['bl_pola_harian'] = (tau.hour >= 13) & (tau.hour < 17)
    f['bl_persistensi'] = (fut.shift(48) == 1).to_numpy()
    f['ada_pwv'] = v.notna().to_numpy()
    return f


def awal_layak(data, kode, f):
    a = pd.read_csv(Path(data) / 'awal_hujan.csv', parse_dates=['waktu_utc'])
    a = a[a.kode_stasiun == kode].copy()
    a['jam'] = (a.waktu_utc + WIB).dt.hour
    a = a[(a.jam >= 6) & (a.jam < 18)]
    ada = f.ada_pwv
    keep = [ada[(ada.index >= t - pd.Timedelta(hours=3)) & (ada.index < t)].sum() >= 4 for t in a.waktu_utc]
    a = a[keep].copy(); a['bulan'] = (a.waktu_utc + WIB).dt.month
    return a


# ---------------------------------------------------------------- simulasi status + pesan (kode mesin)
def simulasi(f, syarat2, ada, aturan):
    """Jalankan PenilaiAturan dan kebijakan pesan untuk satu chat. Kembali (status_on, indeks BERPOTENSI terkirim)."""
    pen = PenilaiAturan(aturan); kuota = KuotaMemori()
    tau = f.index + SETENGAH
    on = np.zeros(len(f), bool); kirim = []; sebelum = pen.level
    for i in range(len(f)):
        lv = pen.langkah(bool(syarat2[i]), False, bool(ada[i]))
        on[i] = lv == 'BERPOTENSI'
        j = transisi(sebelum, lv)
        if j:
            h = kuota.putuskan(j, tau[i], aturan)
            if j == 'BERPOTENSI' and h and h[0] == 'DIJADWALKAN':
                kirim.append(i)
        sebelum = lv
    return on, np.array(kirim, int)


def syarat_aturan(f, a):
    x = f[a.jenis].to_numpy() if a.l2_min is not None else None
    s = np.ones(len(f), bool) if x is None else np.nan_to_num(x, nan=-1e9) >= a.l2_min
    if a.l2_delta is not None:
        s &= np.nan_to_num(f.delta_3j.to_numpy(), nan=-1e9) >= a.l2_delta
    return s


def nilai(f, st, kirim, awal):
    """Komponen skor per bulan untuk satu stasiun."""
    out = {}
    nilai_ok = f.siang & f.anomali.notna() & f.hujan_3j_depan.notna()
    o = (f.hujan_3j_depan == 1).to_numpy()
    tau_kirim = f.index[kirim] + SETENGAH
    basah = (f.hujan_mm_per_jam >= BASAH).to_numpy()
    palsu = np.array([not basah[i + 1:i + 7].any() for i in kirim], bool)
    for bln in (9, 10):
        m = (nilai_ok & (f.bulan == bln)).to_numpy()
        H = int((st & o & m).sum()); F = int((st & ~o & m).sum()); M = int((~st & o & m).sum()); CN = int((~st & ~o & m).sum())
        aw = awal[awal.bulan == bln]
        hit, lead, tercakup = 0, [], 0
        for t in aw.waktu_utc:
            w = tau_kirim[(tau_kirim <= t) & (tau_kirim >= t - pd.Timedelta(hours=3))]
            if len(w): hit += 1; lead.append((t - w.min()).total_seconds() / 60)
            j = f.index.get_indexer([t - SETENGAH])[0]
            if j >= 0 and st[j]: tercakup += 1
        # notifikasi per hari: pembilang dan penyebut memakai hari yang sama (hari dengan PWV siang). Tanpa ini,
        # pembanding tanpa PWV (pola harian) juga menghitung notifikasi di hari tanpa data -> > 1 per hari.
        hari_dinilai = set(f[(f.bulan == bln) & f.siang & f.ada_pwv].tanggal_wib)
        kb = np.array([t in hari_dinilai for t in f.tanggal_wib.to_numpy()[kirim]], bool) if len(kirim) else \
            np.zeros(0, bool)
        hari = len(hari_dinilai)
        out[bln] = dict(H=H, F=F, M=M, CN=CN, awal=len(aw), tertangkap=hit, tercakup=tercakup, lead=lead,
                        kirim=int(kb.sum()), kirim_palsu=int(palsu[kb].sum()), hari=hari)
    return out


def skor(k):
    H, F, M, CN = k['H'], k['F'], k['M'], k['CN']; n = H + F + M + CN
    den = (H + M) * (M + CN) + (H + F) * (F + CN)
    return dict(n=n, nyala=(H + F) / n if n else np.nan, POD=H / (H + M) if H + M else np.nan,
                FAR=F / (H + F) if H + F else np.nan, CSI=H / (H + F + M) if H + F + M else np.nan,
                HSS=2 * (H * CN - F * M) / den if den else np.nan,
                E3J=f"{k['tertangkap']}/{k['awal']}", E3J_frac=k['tertangkap'] / k['awal'] if k['awal'] else np.nan,
                tercakup=f"{k['tercakup']}/{k['awal']}",
                lead_med=float(np.median(k['lead'])) if k['lead'] else np.nan,
                kirim_per_hari=k['kirim'] / k['hari'] if k['hari'] else np.nan,
                kirim_palsu_frac=k['kirim_palsu'] / k['kirim'] if k['kirim'] else np.nan)


def jumlah(blok):
    tot = dict(H=0, F=0, M=0, CN=0, awal=0, tertangkap=0, tercakup=0, lead=[], kirim=0, kirim_palsu=0, hari=0)
    for k in blok:
        for x in tot:
            tot[x] = tot[x] + k[x]
    return tot


def daftar_aturan():
    d_opsi = [None, 0, 2, 4, 6]
    out = [('anomali', a, d) for a in [None, -2, 0, 2, 4, 6, 8, 10, 11, 12, 13, 14, 16, 18, 20] for d in d_opsi
           if not (a is None and d is None)]
    out += [('persentil', p, d) for p in [50, 60, 70, 75, 80, 85, 90, 95] for d in d_opsi]
    return out


def jalankan_grid(data):
    hasil, fitur_simpan = {}, []
    for W in (7, 15):
        for kode in STASIUN:
            f = fitur_stasiun(data, kode, W)
            if W == 15: fitur_simpan.append(f)
            aw = awal_layak(data, kode, f); ada = f.ada.to_numpy()
            for (fam, x, d) in daftar_aturan():
                a = aturan_uji(fam, x, d, W)
                st, kirim = simulasi(f, syarat_aturan(f, a), ada, a)
                hasil[(W, fam, x, d, kode)] = nilai(f, st, kirim, aw)
            a0 = aturan_uji('anomali', None, None, W)
            for nama in ('bl_pola_harian', 'bl_persistensi'):
                st, kirim = simulasi(f, f[nama].to_numpy(), np.ones(len(f), bool), a0)
                hasil[(W, nama, None, None, kode)] = nilai(f, st, kirim, aw)
            st, kirim = simulasi(f, np.nan_to_num(f.pwv_1jam.to_numpy(), nan=0) >= 45, ada, a0)
            hasil[(W, 'ambang_45', 45, None, kode)] = nilai(f, st, kirim, aw)
    return hasil, pd.concat(fitur_simpan)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('data', nargs='?', default=None, help='folder berisi pwv_30menit_*.csv, hujan_30menit.csv, awal_hujan.csv')
    ap.add_argument('--keluar', default=str(AKAR / 'data' / 'evaluasi'))
    ap.add_argument('--aturan', default=str(AKAR / 'config' / 'aturan.yaml'))
    x = ap.parse_args()
    data = Path(x.data) if x.data else None
    if data is None:            # susunan repo: data/pwv dan data/hujan digabung sementara
        import tempfile
        data = Path(tempfile.mkdtemp(prefix='kalibrasi_'))
        for f in list((AKAR / 'data' / 'pwv').glob('pwv_30menit_*.csv')) + list((AKAR / 'data' / 'hujan').glob('*.csv')):
            (data / f.name).write_bytes(f.read_bytes())
    keluar = Path(x.keluar); keluar.mkdir(parents=True, exist_ok=True)

    hasil, fitur = jalankan_grid(data)
    fitur.rename_axis('waktu_utc').to_csv(keluar / 'fitur.csv', float_format='%.2f')
    kunci = sorted({k[:4] for k in hasil if k[1] in ('anomali', 'persentil')}, key=str)

    def gabung(k, stasiun, bulan):
        return skor(jumlah([hasil[k + (s,)][b] for s in stasiun for b in bulan]))

    def pilih(stasiun, bulan, calon=None):
        return max(calon or kunci, key=lambda k: np.nan_to_num(gabung(k, stasiun, bulan)['HSS'], nan=-9))

    g = []
    for k in kunci:
        r = gabung(k, STASIUN, (9, 10)); r.update(W=k[0], keluarga=k[1], x=k[2], d=k[3]); g.append(r)
    pd.DataFrame(g).sort_values('HSS', ascending=False).to_csv(keluar / 'grid_skor.csv', index=False, float_format='%.4f')

    baris = []
    def catat(skema, uji, k, stasiun, bulan, kalib=''):
        r = gabung(k, stasiun, bulan)
        r.update(skema=skema, uji=uji, aturan=f'{k[1]} x={k[2]} d={k[3]} W={k[0]}', dikalibrasi_pada=kalib); baris.append(r)
    blines = [(15, 'bl_pola_harian', None, None), (15, 'bl_persistensi', None, None), (15, 'ambang_45', 45, None)]
    loso = []
    for s in STASIUN:
        latih = [y for y in STASIUN if y != s]; k = pilih(latih, (9, 10))
        catat('LOSO', s, k, [s], (9, 10), '+'.join(latih)); loso += [hasil[k + (s,)][b] for b in (9, 10)]
        for bl in blines: catat('LOSO', s, bl, [s], (9, 10))
    r = skor(jumlah(loso)); r.update(skema='LOSO', uji='GABUNGAN', aturan='aturan terpilih per lipatan', dikalibrasi_pada='3 stasiun lain')
    baris.append(r); r_loso = r
    for bl in blines: catat('LOSO', 'GABUNGAN', bl, STASIUN, (9, 10))
    k = pilih(STASIUN, (9,)); catat('SEP->OKT', 'Oktober, 4 stasiun', k, STASIUN, (10,), 'September, 4 stasiun')
    for bl in blines: catat('SEP->OKT', 'Oktober, 4 stasiun', bl, STASIUN, (10,))
    # Keluarga aturan dipilih dari skor uji silang (di luar sampel); parameternya dari semua data.
    per_kel = {}
    for fam in ('anomali', 'persentil'):
        calon = [k2 for k2 in kunci if k2[1] == fam]; blok, pilihan = [], []
        for s in STASIUN:
            latih = [y for y in STASIUN if y != s]; k2 = pilih(latih, (9, 10), calon)
            blok += [hasil[k2 + (s,)][b] for b in (9, 10)]; pilihan.append(f'{s}:{k2[2]}/{k2[3]}/W{k2[0]}')
        r = skor(jumlah(blok)); per_kel[fam] = r
        r.update(skema='LOSO per keluarga', uji='GABUNGAN', aturan=f'{fam} (' + ', '.join(pilihan) + ')',
                 dikalibrasi_pada='3 stasiun lain'); baris.append(r)
    # HSS dibulatkan 2 desimal; bila seri, pilih yang memperingatkan lebih banyak awal hujan (E-3J).
    fam_terbaik = max(per_kel, key=lambda fm: (round(per_kel[fm]['HSS'], 2), per_kel[fm]['E3J_frac']))
    r_loso = per_kel[fam_terbaik]
    # Parameter final memakai aturan seri yang sama: HSS 2 desimal, lalu E-3J terbanyak.
    kf = max([k2 for k2 in kunci if k2[1] == fam_terbaik],
             key=lambda k2: (round(np.nan_to_num(gabung(k2, STASIUN, (9, 10))['HSS'], nan=-9), 2),
                             gabung(k2, STASIUN, (9, 10))['E3J_frac']))
    catat('FINAL in-sample', 'semua', kf, STASIUN, (9, 10), 'semua data')
    for s in STASIUN: catat('FINAL in-sample', s, kf, [s], (9, 10), 'semua data')
    v = pd.DataFrame(baris)
    kol = ['skema', 'uji', 'aturan', 'dikalibrasi_pada', 'n', 'nyala', 'POD', 'FAR', 'CSI', 'HSS', 'E3J', 'tercakup',
           'lead_med', 'kirim_per_hari', 'kirim_palsu_frac']
    v[kol].round(4).to_csv(keluar / "validasi.csv", index=False)
    pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 40)
    print(v[kol].round(2).to_string(index=False))

    W, fam, xx, d = kf
    pemb = {nm: round(float(v[(v.skema == 'LOSO') & (v.uji == 'GABUNGAN') & v.aturan.str.startswith(nm)].HSS.iloc[0]), 2)
            for nm in ('bl_pola_harian', 'bl_persistensi', 'ambang_45')}
    uji = {}
    for k2 in ('HSS', 'POD', 'FAR', 'nyala', 'E3J', 'tercakup', 'kirim_per_hari'):
        val = r_loso[k2]
        uji[k2] = round(float(val), 2) if isinstance(val, (float, np.floating)) else val
    cfg = {
        'nama': f'{fam}-{xx:g}' + (f'-naik{d:g}' if d is not None else ''),
        'versi': '1.2.0',
        'dibuat': str(pd.Timestamp.now(tz='Asia/Jakarta').date()),
        'fitur': {'jendela_acuan_hari': int(W), 'min_hari_acuan': 3,
                  'reset_acuan': {k2: t.strftime('%Y-%m-%dT%H:%M:%SZ') for k2, t in RESET.items()}},
        'level2': {'jenis': fam, 'min': xx, 'delta3j_min_mm': d, 'padam_setelah_menit': 60},
        'level1': {'jenis': fam, 'min': (xx / 2 if fam == 'anomali' else max(xx - 15, 0))},
        'tanpa_data_setelah_menit': 120,
        'notifikasi': {'jam_mulai_wib': '06:00', 'jam_selesai_wib': '18:00', 'maks_per_hari': 2,
                       'kuota_mencakup': ['BERPOTENSI', 'AMAN_LAGI'], 'tanya_hujan_setelah_menit': 90,
                       'aman_lagi_sampai_wib': '15:00'},
        'kalibrasi': {
            'data': ('CKRG, BAKO, CLBG, CJUR; 1 Sep–1 Nov 2026; ERA5 1 Sep–28 Okt 09 UTC dan 1–3 Nov; '
                     '28 Okt 10 UTC–31 Okt 23 UTC diisi pola harian + anomali antar-tepi (METEO_ISI)'),
            'sasaran': 'HSS P-3J tertinggi (hujan IMERG >= 1 mm/jam dalam 3 jam, keputusan 06.00–17.30 WIB)',
            'skor_uji_silang_per_stasiun': uji,
            'pembanding_HSS': pemb,
            'rincian': 'data/evaluasi/validasi.csv',
        },
    }
    kepala = ('# Aturan peringatan AngkatDulu. Ditulis oleh pipeline/evaluasi/kalibrasi.py; dibaca mesin (PenilaiAturan).\n'
              '# Celah ERA5 28–31 Okt diisi (pipeline/pwv/pwv.py, galat PWV rata-rata 0,26 mm). Level 1 belum dikalibrasi terpisah.\n')
    Path(x.aturan).write_text(kepala + yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding='utf-8')
    print(f'\nAturan final: {cfg["nama"]} -> {x.aturan}')


if __name__ == '__main__':
    main()
