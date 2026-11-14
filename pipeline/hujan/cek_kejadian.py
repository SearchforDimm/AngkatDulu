"""Hitung awal hujan siang (06–18 WIB) yang punya PWV cukup di 3 jam sebelumnya, per stasiun dan bulan.

python3 cek_kejadian.py awal_hujan.csv pwv_30menit_<st>.csv [...]
"""
import sys
import pandas as pd

PAKAI = ['OK', 'METEO_ISI', 'ORBIT_RAPID']
a = pd.read_csv(sys.argv[1], parse_dates=['waktu_utc', 'jam_wib'])
baris = []
for f in sys.argv[2:]:
    p = pd.read_csv(f, parse_dates=['waktu_utc'])
    kode = p.kode_stasiun.iloc[0]
    ok = p[p.flag_kualitas.isin(PAKAI)].waktu_utc
    e = a[(a.kode_stasiun == kode) & a.jam_wib.dt.hour.between(6, 17)]
    for _, r in e.iterrows():
        n = ((ok >= r.waktu_utc - pd.Timedelta(hours=3)) & (ok < r.waktu_utc)).sum()
        baris.append(dict(stasiun=kode, bulan=r.jam_wib.strftime('%b'), ada_pwv=n >= 4))
d = pd.DataFrame(baris)
t = d.pivot_table(index='stasiun', columns='bulan', values='ada_pwv', aggfunc=['sum', 'count'], fill_value=0)
t.columns = [f'{"bisa_dipakai" if a == "sum" else "semua"}_{b}' for a, b in t.columns]
t.loc['TOTAL'] = t.sum()
print(t.astype(int).to_string())
