"""Ekstrak ZTD 30 detik dari out26/*.pos.stat untuk satu stasiun (hanya 00–24 UTC hari D).

python3 ekstrak_ztd.py STASIUN DOY_AWAL DOY_AKHIR  -> ztd_<stasiun>.csv + qc_<stasiun>.csv
Kolom flag: OK | KONVERGENSI (1 jam pertama bila hari sebelumnya tidak ada) | ORBIT_RAPID
"""
import os, sys
import numpy as np, pandas as pd

GPS0 = pd.Timestamp('1980-01-06')


def produk_hari(doy):
    for pre in ('COD0MGXFIN', 'COD0OPSFIN', 'COD0OPSRAP'):
        if os.path.exists(f'prod/{pre}_2026{doy:03d}0000_01D_05M_ORB.SP3'):
            return pre
    return None


def main():
    st, d0, d1 = sys.argv[1].lower(), int(sys.argv[2]), int(sys.argv[3])
    semua, qc = [], []
    for d in range(d0, d1 + 1):
        f = f'out26/{st}{d:03d}.pos'
        if not os.path.exists(f + '.stat'):
            continue
        hari = pd.Timestamp('2026-01-01') + pd.Timedelta(days=d - 1)
        tr = [l.strip().split(',') for l in open(f + '.stat') if l.startswith('$TROP')]
        if not tr:
            qc.append(dict(doy=d, tanggal=hari.date(), status='KOSONG'))
            continue
        t = np.array([GPS0 + pd.Timedelta(seconds=int(x[1]) * 604800 + float(x[2]) - 18) for x in tr])
        z = np.array([float(x[5]) for x in tr]); s = np.array([float(x[6]) for x in tr])
        df = pd.DataFrame({'waktu_utc': t, 'ztd_m': z, 'sigma_m': s})
        df = df[(df.waktu_utc >= hari) & (df.waktu_utc < hari + pd.Timedelta(days=1))]
        jendela = bool(t.min() < hari - pd.Timedelta(minutes=30))   # ada data hari sebelumnya → jendela 26 jam
        pre = produk_hari(d)
        df['flag'] = 'ORBIT_RAPID' if pre == 'COD0OPSRAP' else 'OK'
        if not jendela:
            df.loc[df.waktu_utc < hari + pd.Timedelta(hours=1), 'flag'] = 'KONVERGENSI'
        df['produk'] = pre
        pos = [l.split() for l in open(f) if not l.startswith('%')]
        ns = [int(p[6]) for p in pos if pd.Timestamp(p[0].replace('/', '-') + ' ' + p[1]) >= hari]
        ok = df[df.flag != 'KONVERGENSI']
        qc.append(dict(doy=d, tanggal=hari.date(), status='OK', jendela_26j=bool(jendela), produk=pre,
                       epoch=len(df), satelit_rata2=round(float(np.mean(ns)), 1) if ns else None,
                       sigma_ztd_mm=round(ok.sigma_m.mean() * 1000, 1),
                       ztd_rata2_m=round(ok.ztd_m.mean(), 4), ztd_min=round(ok.ztd_m.min(), 4), ztd_maks=round(ok.ztd_m.max(), 4)))
        semua.append(df)
    pd.concat(semua).to_csv(f'ztd_{st}.csv', index=False)
    q = pd.DataFrame(qc); q.to_csv(f'qc_{st}.csv', index=False)
    print(q.to_string(index=False))


if __name__ == '__main__':
    main()
