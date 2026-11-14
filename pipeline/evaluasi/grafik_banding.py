"""Grafik banding aturan (HSS uji silang per stasiun) dari validasi.csv dan banding_gabungan.csv.

python pipeline/evaluasi/grafik_banding.py [FOLDER_EVALUASI]  -> banding_aturan.png
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

d = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / 'data' / 'evaluasi'
b = pd.read_csv(d / 'banding_gabungan.csv').set_index('keluarga')
v = pd.read_csv(d / 'validasi.csv')
L = v[(v.skema == 'LOSO') & (v.uji == 'GABUNGAN')]
def baris(awalan, skema='LOSO'):
    d = v[(v.skema == skema) & (v.uji == 'GABUNGAN') & v.aturan.str.startswith(awalan)].iloc[0]
    return d.HSS, d.E3J, d.kirim_per_hari
# pembanding tunggal dan aturan aktif dari validasi.csv (sama dengan Tabel 1 proposal); gabungan dari banding_gabungan.csv
rows = [('Pola harian (tiap 13–17 WIB)', *baris('bl_pola_harian'), 'base'),
        ('Ambang tetap PWV ≥ 45 mm', *baris('ambang_45'), 'pwv'),
        ('PWV ≥ persentil 80 stasiun', *baris('persentil', 'LOSO per keluarga'), 'pwv'),
        ('Persistensi (hujan kemarin, jam sama)', *baris('bl_persistensi'), 'base'),
        ('PWV ≥ persentil 60 DAN persistensi', b.loc['pct&pers', 'LOSO_HSS'], b.loc['pct&pers', 'LOSO_E3J'], b.loc['pct&pers', 'LOSO_kirim'], 'pwv')]
fig, ax = plt.subplots(figsize=(10, 3.6))
y = list(range(len(rows)))[::-1]
for yi, (lab, h, e, k, jenis) in zip(y, rows):
    ax.barh(yi, h, height=0.55, color='#2a78d6' if jenis == 'pwv' else '#b8b7b0')
    ax.text(h + 0.008, yi, f'{h:.2f}'.replace('.', ','), va='center', fontsize=10, color='#1f1f1e')
    ax.text(0.62, yi, f'{e}', va='center', fontsize=9.5, color='#5f5e5a')
    ax.text(0.75, yi, f'{k:.2f}'.replace('.', ','), va='center', fontsize=9.5, color='#5f5e5a')
ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows], fontsize=10, color='#1f1f1e')
ax.text(0.62, len(rows) - 0.35, 'awal hujan\ndiperingatkan', fontsize=8.5, color='#5f5e5a', va='bottom')
ax.text(0.75, len(rows) - 0.35, 'notifikasi\nper hari', fontsize=8.5, color='#5f5e5a', va='bottom')
ax.set_xlim(0, 0.85); ax.set_xticks([0, 0.1, 0.2, 0.3, 0.4, 0.5])
ax.set_xticklabels(['0', '0,1', '0,2', '0,3', '0,4', '0,5'])
ax.set_xlabel('HSS: hujan ≥ 1 mm/jam dalam 3 jam ke depan (uji silang per stasiun)', fontsize=9, color='#5f5e5a', loc='left')
for s in ('top', 'right', 'left'): ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color('#bdbcb5'); ax.tick_params(axis='x', colors='#5f5e5a', labelsize=8); ax.tick_params(axis='y', length=0)
ax.grid(axis='x', color='#e6e5e0', lw=0.6); ax.set_axisbelow(True)
fig.suptitle('Kalibrasi aturan: 4 stasiun, 1 Sep–1 Nov 2026, 66 awal hujan siang', x=0.01, ha='left', fontsize=12, color='#1f1f1e')
fig.text(0.01, -0.09, 'Biru = memakai PWV GNSS. Abu-abu = pembanding tanpa PWV. Parameter dipilih di 3 stasiun, diuji di stasiun ke-4, bergantian.',
         fontsize=8, color='#5f5e5a')
fig.savefig(d / 'banding_aturan.png', dpi=140, bbox_inches='tight', facecolor='white')
print(d / 'banding_aturan.png')
