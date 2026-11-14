"""Tahap 7: bangun angkatdulu.db dari skema.sql dan hasil pemrosesan (FR-01).

python db/impor.py                      # dari folder repo; menulis angkatdulu.db (file DB tidak di-commit)
python db/impor.py --db lain.db --aturan config/aturan.yaml

Isi: stasiun (4 stasiun yang punya PWV), run_pengolahan, observasi_pwv, observasi_hujan, awal_hujan, aturan.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AKAR))
from mesin.basisdata import buka, muat_aturan  # noqa: E402
from mesin.waktu import iso  # noqa: E402

STASIUN = {   # kode: (nama, lat, lon, tinggi elipsoid m, tinggi ortometrik EGM96 m)
    'CKRG': ('Karawang', -6.11118, 107.32803, 27.6, 8.0),
    'BAKO': ('Cibinong', -6.49110, 106.84890, 158.19, 140.1),
    'CLBG': ('Lembang', -6.82444, 107.61560, 1329.83, 1308.9),
    'CJUR': ('Cianjur', -6.82209, 107.13815, 479.9, 459.8),
}


def _run_dari_id(run_id):
    """'pwv-20261102-1649' (WIB) -> waktu UTC."""
    t = pd.to_datetime(run_id.split('-', 1)[1], format='%Y%m%d-%H%M') - pd.Timedelta(hours=7)
    return iso(t.tz_localize('UTC'))


def bangun(db, akar=AKAR, aturan=None, timpa=True):
    db = Path(db); akar = Path(akar)
    if db.exists():
        if not timpa:
            raise FileExistsError(db)
        db.unlink()
    con = buka(db)
    con.executescript((akar / 'db' / 'skema.sql').read_text(encoding='utf-8'))
    sekarang = iso(pd.Timestamp.now(tz='UTC'))
    for kode, (nama, lat, lon, he, ho) in STASIUN.items():
        con.execute("INSERT INTO stasiun VALUES (?, ?, ?, ?, ?, ?, 'SEHAT', ?)", (kode, nama, lat, lon, he, ho, sekarang))

    # PWV
    pwv = pd.concat([pd.read_csv(f) for f in sorted((akar / 'data' / 'pwv').glob('pwv_30menit_*.csv'))])
    for run_id, g in pwv.groupby('run_id'):
        con.execute("INSERT INTO run_pengolahan VALUES (?, 'PWV', ?, ?, ?, ?, ?, ?, ?)",
                    (run_id, 'RTKLIB-EX 2.5.1 PPP-fixed GPS+GLONASS; ERA5; Saastamoinen + Bevis', 'pipeline/pwv/pwv.py',
                     g.waktu_utc.min(), g.waktu_utc.max(), _run_dari_id(run_id), _run_dari_id(run_id),
                     'stasiun ' + ', '.join(sorted(g.kode_stasiun.unique()))))
    kol = ['kode_stasiun', 'waktu_utc', 'run_id', 'pwv_mm', 'sigma_pwv_mm', 'ztd_m', 'zhd_m', 'zwd_m', 'tekanan_hpa',
           'suhu_k', 'tm_k', 'n_epoch', 'sumber_meteo', 'produk_orbit', 'flag_kualitas']
    con.executemany(f'INSERT INTO observasi_pwv ({", ".join(kol)}) VALUES ({", ".join("?" * len(kol))})',
                    pwv[kol].astype(object).where(pwv[kol].notna(), None).itertuples(index=False, name=None))

    # Hujan dan awal hujan (hanya untuk evaluasi, rekam jejak, dan grafik)
    h = pd.read_csv(akar / 'data' / 'hujan' / 'hujan_30menit.csv')
    h = h[h.kode_stasiun.isin(STASIUN)]
    con.execute("INSERT INTO run_pengolahan VALUES ('imerg-late-v07', 'HUJAN', 'IMERG Late Run v07 (Giovanni)', "
                "'pipeline/hujan/hujan.py', ?, ?, ?, ?, 'sel IMERG di atas stasiun')",
                (h.waktu_utc.min(), h.waktu_utc.max(), sekarang, sekarang))
    con.executemany("INSERT INTO observasi_hujan VALUES (?, ?, 'IMERG_LATE_V07', 0, ?, 'imerg-late-v07')",
                    ((r.kode_stasiun, r.waktu_utc, None if pd.isna(r.hujan_mm_per_jam) else float(r.hujan_mm_per_jam))
                     for r in h.itertuples()))
    a = pd.read_csv(akar / 'data' / 'hujan' / 'awal_hujan.csv')
    a = a[a.kode_stasiun.isin(STASIUN)]
    con.execute("INSERT INTO run_pengolahan VALUES ('awal-hujan-v1', 'AWAL_HUJAN', NULL, 'pipeline/hujan/hujan.py', "
                '?, ?, ?, ?, ?)', (h.waktu_utc.min(), h.waktu_utc.max(), sekarang, sekarang, a.definisi.iloc[0]))
    con.executemany("INSERT INTO awal_hujan (kode_stasiun, waktu_utc, hujan_mm_per_jam, sumber, definisi, run_id) "
                    "VALUES (?, ?, ?, 'IMERG', ?, 'awal-hujan-v1')",
                    a[['kode_stasiun', 'waktu_utc', 'hujan_mm_per_jam', 'definisi']].itertuples(index=False, name=None))
    con.execute("INSERT INTO run_pengolahan VALUES (?, 'IMPOR', NULL, 'db/impor.py', NULL, NULL, ?, ?, NULL)",
                ('impor-' + pd.Timestamp.now(tz='Asia/Jakarta').strftime('%Y%m%d-%H%M%S'), sekarang, sekarang))
    con.commit()
    aturan_obj, aturan_id = muat_aturan(con, aturan or (akar / 'config' / 'aturan.yaml'))
    return con, aturan_obj, aturan_id


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', default=str(AKAR / 'angkatdulu.db'))
    ap.add_argument('--aturan', default=str(AKAR / 'config' / 'aturan.yaml'))
    x = ap.parse_args()
    con, a, aid = bangun(x.db, aturan=x.aturan)
    for t in ('stasiun', 'run_pengolahan', 'observasi_pwv', 'observasi_hujan', 'awal_hujan', 'aturan'):
        print(f'{t:16s} {con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]:>7} baris')
    print(f'aturan aktif: {a.nama} {a.versi} (id {aid})  ->  {x.db}')


if __name__ == '__main__':
    main()
