"""Multi-GNSS saat langit terhalang: GPS saja vs GPS+GLONASS dengan sudut elevasi minimum 30°.

python pipeline/evaluasi/banding_gnss.py ACUAN_ZTD_DIR G30_DIR GR30_DIR [DOY_AWAL DOY_AKHIR]
  ACUAN_ZTD_DIR    : ztd_<st>.csv GPS+GLONASS mask 10° (data/ztd), dianggap acuan
  G30_DIR, GR30_DIR: folder hasil jalankan_ppp.py + ekstrak_ztd.py dengan konfig *_g30.conf / *_gr30.conf
                     (sama dengan fix_*.conf, hanya pos1-elmask = 30 dan, untuk GPS saja, pos1-navsys = 1)
Epoch dianggap gagal bila ZTD tidak ada atau meleset > 100 mm dari acuan. Hasil: data/evaluasi/banding_gnss_mask30.csv.
Hasil 18–27 Okt 2026 (40 hari-stasiun): gagal 26,8% (GPS saja) vs 0,3% (GPS+GLONASS); median |selisih| ±19–20 mm.
"""
import os
import sys

import numpy as np
import pandas as pd

AKAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')


def main():
    acuan, g30, gr30 = sys.argv[1:4]
    d0, d1 = (int(sys.argv[4]), int(sys.argv[5])) if len(sys.argv) > 5 else (291, 300)
    t0 = pd.Timestamp('2026-01-01') + pd.Timedelta(days=d0 - 1)
    t1 = pd.Timestamp('2026-01-01') + pd.Timedelta(days=d1)
    rows = []
    for st in ('ckrg', 'bako', 'clbg', 'cjur'):
        r = pd.read_csv(os.path.join(acuan, f'ztd_{st}.csv'), parse_dates=['waktu_utc']).set_index('waktu_utc')
        r = r[(r.index >= t0) & (r.index < t1)]
        for d, nama in ((g30, 'GPS'), (gr30, 'GPS+GLONASS')):
            z = pd.read_csv(os.path.join(d, f'ztd_{st}.csv'), parse_dates=['waktu_utc']).set_index('waktu_utc')
            z = z[~z.index.duplicated()].reindex(r.index)
            dz = (z.ztd_m - r.ztd_m) * 1000
            hilang = z.ztd_m.isna(); kasar = dz.abs() > 100
            rows.append(dict(st=st, sis=nama, n=len(r), hilang=int(hilang.sum()), kasar=int((kasar & ~hilang).sum()),
                             gagal_pct=100 * (hilang | kasar).mean(), median_abs=np.nanmedian(dz[~kasar].abs())))
    t = pd.DataFrame(rows)
    g = t.groupby('sis')[['n', 'hilang', 'kasar']].sum()
    g['gagal_pct'] = 100 * (g.hilang + g.kasar) / g.n
    print(t.round(2).to_string(index=False)); print(); print(g.round(2))
    t.round(3).to_csv(os.path.join(AKAR, 'data', 'evaluasi', 'banding_gnss_mask30.csv'), index=False)


if __name__ == '__main__':
    main()
