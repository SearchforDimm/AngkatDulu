"""Selang kepercayaan 95% untuk HSS (uji silang antarstasiun) dengan bootstrap per hari-stasiun.

python pipeline/evaluasi/selang_hss.py [DATA_DIR] [N_ULANG]  -> data/evaluasi/selang_hss.csv
Parameter tiap lipatan (stasiun uji) dipilih di 3 stasiun lain, sama seperti kalibrasi.py / banding_gabungan.py,
lalu tetap. Yang diambil ulang adalah hari-stasiun (blok 24 jam), bersamaan untuk semua aturan (berpasangan),
sehingga selisih antar-aturan juga punya selang.
"""
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kalibrasi as K  # noqa: E402

AKAR = K.AKAR
W = 15
P_PCT = [50, 60, 70, 75, 80, 85, 90, 95]
P_GAB = [60, 70, 75, 80, 85, 90]


def folder_data(arg):
    if arg:
        return Path(arg)
    d = Path(tempfile.mkdtemp(prefix='selang_'))
    for f in list((AKAR / 'data' / 'pwv').glob('pwv_30menit_*.csv')) + list((AKAR / 'data' / 'hujan').glob('*.csv')):
        (d / f.name).write_bytes(f.read_bytes())
    return d


def hss(H, F, M, CN):
    den = (H + M) * (M + CN) + (H + F) * (F + CN)
    return np.where(den > 0, 2 * (H * CN - F * M) / np.where(den > 0, den, 1), np.nan)


def main():
    data = folder_data(sys.argv[1] if len(sys.argv) > 1 else None)
    n_ulang = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    a0 = K.aturan_uji('anomali', None, None, W)
    per_slot = {}                      # (stasiun, aturan) -> (hari, on, o) untuk slot yang dinilai
    for s in K.STASIUN:
        f = K.fitur_stasiun(data, s, W); ada = f.ada.to_numpy()
        m = (f.siang & f.anomali.notna() & f.hujan_3j_depan.notna() & f.bulan.isin([9, 10])).to_numpy()
        o = (f.hujan_3j_depan == 1).to_numpy()
        hari = f.tanggal_wib.astype(str).to_numpy()
        pct = np.nan_to_num(f.persentil.to_numpy(), nan=-1); pers = f.bl_persistensi.to_numpy().astype(bool)
        sim = {}
        for p in P_PCT:
            a = K.aturan_uji('persentil', p, None, W)
            sim[('pct', p)] = K.simulasi(f, pct >= p, ada, a)[0]
        for p in P_GAB:
            sim[('gab', p)] = K.simulasi(f, (pct >= p) & pers & ada, ada, K.aturan_uji('persentil', None, None, W))[0]
        sim[('pola', None)] = K.simulasi(f, f.bl_pola_harian.to_numpy(), np.ones(len(f), bool), a0)[0]
        sim[('pers', None)] = K.simulasi(f, pers, np.ones(len(f), bool), a0)[0]
        sim[('a45', None)] = K.simulasi(f, np.nan_to_num(f.pwv_1jam.to_numpy(), nan=0) >= 45, ada, a0)[0]
        for k, on in sim.items():
            per_slot[(s, k)] = (hari[m], on[m], o[m])

    def tabel(s, k):
        hari, on, o = per_slot[(s, k)]
        d = pd.DataFrame({'hari': hari, 'H': on & o, 'F': on & ~o, 'M': ~on & o, 'CN': ~on & ~o}).groupby('hari').sum()
        d.index = s + '|' + d.index
        return d

    def total_hss(s_list, k):
        t = sum(tabel(s, k)[['H', 'F', 'M', 'CN']].sum() for s in s_list)
        return float(hss(t.H, t.F, t.M, t.CN))

    # pilihan parameter per lipatan (stasiun uji) dari 3 stasiun lain; seri 2 desimal -> ambang lebih rendah
    pilih = {}
    for fam, opsi in (('pct', P_PCT), ('gab', P_GAB)):
        for s in K.STASIUN:
            latih = [x for x in K.STASIUN if x != s]
            pilih[(fam, s)] = max(opsi, key=lambda p: (round(total_hss(latih, (fam, p)), 4), -p))
    aturan = {'Tebakan jam rawan': lambda s: ('pola', None), 'Ambang PWV ≥ 45 mm': lambda s: ('a45', None),
              'PWV ≥ persentil 80 (aktif)': lambda s: ('pct', pilih[('pct', s)]),
              'Tebakan "kemarin hujan"': lambda s: ('pers', None),
              'PWV ≥ persentil 60 dan "kemarin hujan"': lambda s: ('gab', pilih[('gab', s)])}
    blok = {nm: pd.concat([tabel(s, fn(s)) for s in K.STASIUN]) for nm, fn in aturan.items()}
    idx = blok['Tebakan jam rawan'].index
    blok = {nm: b.reindex(idx).fillna(0).to_numpy() for nm, b in blok.items()}
    rng = np.random.default_rng(2026)
    pilihan = rng.integers(0, len(idx), size=(n_ulang, len(idx)))
    boot, titik = {}, {}
    for nm, b in blok.items():
        t = b.sum(0); titik[nm] = float(hss(*t))
        bs = np.stack([np.bincount(pilihan[r], minlength=len(idx)) @ b for r in range(n_ulang)])
        boot[nm] = hss(bs[:, 0], bs[:, 1], bs[:, 2], bs[:, 3])
    baris = []
    for nm in aturan:
        lo, hi = np.nanpercentile(boot[nm], [2.5, 97.5])
        baris.append(dict(aturan=nm, HSS=titik[nm], bawah=lo, atas=hi))
    akt = 'PWV ≥ persentil 80 (aktif)'
    for a, b in ((akt, 'Tebakan jam rawan'), (akt, 'Ambang PWV ≥ 45 mm'), (akt, 'Tebakan "kemarin hujan"'),
                 ('PWV ≥ persentil 60 dan "kemarin hujan"', 'Tebakan "kemarin hujan"')):
        d = boot[a] - boot[b]; lo, hi = np.nanpercentile(d, [2.5, 97.5])
        baris.append(dict(aturan=f'selisih: {a} − {b}', HSS=titik[a] - titik[b], bawah=lo, atas=hi,
                          p_lebih_baik=float(np.nanmean(d > 0))))
    out = pd.DataFrame(baris)
    keluar = AKAR / 'data' / 'evaluasi' / 'selang_hss.csv'
    out.round(3).to_csv(keluar, index=False)
    print(f'{len(idx)} hari-stasiun, {n_ulang} ulangan; pilihan lipatan:', pilih)
    print(out.round(3).to_string(index=False))


if __name__ == '__main__':
    main()
