"""Bandingkan aturan gabungan: PWV + jendela jam, PWV + persistensi (LOSO dan Sep->Okt).

python banding_gabungan.py DATA_DIR [KELUAR.csv]  -> banding_gabungan.csv
Memakai simulasi status + kebijakan pesan yang sama dengan mesin (kalibrasi.simulasi).
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent)); import kalibrasi as K
from pathlib import Path
data = Path(sys.argv[1]); W = 15
F = {s: K.fitur_stasiun(data, s, W) for s in K.STASIUN}
A = {s: K.awal_layak(data, s, F[s]) for s in K.STASIUN}
def run(fn):
    out = {}
    for s in K.STASIUN:
        f = F[s]; ada = f.ada.to_numpy()
        st, kirim = K.simulasi(f, fn(f) & ada, ada, K.aturan_uji('persentil', None, None, W))
        out[s] = K.nilai(f, st, kirim, A[s])
    return out
rules = {}
pct = lambda f: np.nan_to_num(f.persentil.to_numpy(), nan=-1)
jam = lambda f: f.jam_wib.to_numpy()
pers = lambda f: f.bl_persistensi.to_numpy().astype(bool)
for p in (60, 70, 75, 80, 85, 90):
    rules[('pct', p, None)] = (lambda p: lambda f: pct(f) >= p)(p)
    for j0 in (10, 11, 12, 13):
        rules[('pct+jam', p, j0)] = (lambda p, j0: lambda f: (pct(f) >= p) & (jam(f) >= j0) & (jam(f) < 17))(p, j0)
    rules[('pct&pers', p, None)] = (lambda p: lambda f: (pct(f) >= p) & pers(f))(p)
    rules[('pct|pers', p, None)] = (lambda p: lambda f: (pct(f) >= p) | pers(f))(p)
for j0 in (10, 11, 12, 13):
    rules[('jam', None, j0)] = (lambda j0: lambda f: (jam(f) >= j0) & (jam(f) < 17))(j0)
    rules[('pers+jam', None, j0)] = (lambda j0: lambda f: pers(f) & (jam(f) >= j0) & (jam(f) < 17))(j0)
rules[('pers', None, None)] = lambda f: pers(f)
R = {k: run(fn) for k, fn in rules.items()}
def g(k, st, bl): return K.skor(K.jumlah([R[k][s][b] for s in st for b in bl]))
fams = sorted({k[0] for k in R})
rows = []
for fam in fams:
    ks = [k for k in R if k[0] == fam]
    # LOSO dengan pilihan parameter di dalam keluarga
    blok = []
    for s in K.STASIUN:
        tr = [x for x in K.STASIUN if x != s]
        kb = max(ks, key=lambda k: np.nan_to_num(g(k, tr, (9, 10))['HSS'], nan=-9))
        blok += [R[kb][s][b] for b in (9, 10)]
    lo = K.skor(K.jumlah(blok))
    ks_sep = max(ks, key=lambda k: np.nan_to_num(g(k, K.STASIUN, (9,))['HSS'], nan=-9)); so = g(ks_sep, K.STASIUN, (10,))
    kf = max(ks, key=lambda k: (round(np.nan_to_num(g(k, K.STASIUN, (9, 10))['HSS'], nan=-9), 2),   # seri: E-3J
                                g(k, K.STASIUN, (9, 10))['E3J_frac'])); ins = g(kf, K.STASIUN, (9, 10))
    rows.append(dict(keluarga=fam, LOSO_nyala=lo['nyala'], LOSO_HSS=lo['HSS'], LOSO_POD=lo['POD'], LOSO_FAR=lo['FAR'], LOSO_E3J=lo['E3J'], LOSO_kirim=lo['kirim_per_hari'], LOSO_palsu=lo['kirim_palsu_frac'],
                     SepOkt_HSS=so['HSS'], SepOkt_E3J=so['E3J'], final=str(kf[1:]), ins_HSS=ins['HSS'], ins_E3J=ins['E3J'], ins_kirim=ins['kirim_per_hari'], ins_nyala=ins['nyala']))
pd.set_option('display.width', 250)
hasil = pd.DataFrame(rows).round(3).sort_values('LOSO_HSS', ascending=False); hasil.to_csv(sys.argv[2] if len(sys.argv) > 2 else 'banding_gabungan.csv', index=False); print(hasil.round(2).to_string(index=False))
