"""Ekspor log replay ke CSV (FR-13): status, peringatan, pesan, umpan balik."""
from pathlib import Path

import pandas as pd

from .waktu import WIB


def _wib(df, kolom):
    for k in kolom:
        if k in df and df[k].notna().any():
            df[k.replace('_utc', '_wib')] = (pd.to_datetime(df[k], utc=True).dt.tz_localize(None) + WIB).dt.strftime('%Y-%m-%d %H:%M')
    return df


def ekspor_sesi(con, sesi_id, folder):
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    tabel = {
        'status': ('SELECT * FROM status_stasiun WHERE sesi_id = ? ORDER BY kode_stasiun, waktu_utc', ['waktu_utc']),
        'peringatan': ('SELECT * FROM peringatan WHERE sesi_id = ? ORDER BY mulai_utc', ['mulai_utc', 'selesai_utc']),
        'pesan': ('SELECT * FROM pesan WHERE sesi_id = ? ORDER BY dijadwalkan_utc, id', ['dijadwalkan_utc', 'terkirim_utc']),
        'umpan_balik': ('SELECT u.* FROM umpan_balik u JOIN pesan p ON p.id = u.pesan_id WHERE p.sesi_id = ?', ['waktu_utc']),
    }
    hasil = {}
    for nama, (sql, kolom) in tabel.items():
        df = _wib(pd.read_sql_query(sql, con, params=(sesi_id,)), kolom)
        path = folder / f'sesi{sesi_id}_{nama}.csv'; df.to_csv(path, index=False); hasil[nama] = path
    return hasil
