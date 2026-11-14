"""Koneksi database dan pemuatan aturan (US-10: aturan baru = baris baru di tabel aturan)."""
import sqlite3

import pandas as pd

from .aturan import Aturan
from .waktu import iso


def buka(path):
    con = sqlite3.connect(str(path))
    con.execute('PRAGMA foreign_keys = ON')
    return con


def muat_aturan(con, path_yaml):
    """Baca aturan.yaml; tambahkan ke tabel `aturan` bila (nama, versi) belum ada. Kembali (Aturan, aturan_id)."""
    a = Aturan.dari_yaml(path_yaml)
    ada = con.execute('SELECT id FROM aturan WHERE nama = ? AND versi = ?', (a.nama, a.versi)).fetchone()
    if ada:
        return a, ada[0]
    kal = (a.asli.get('kalibrasi') or {}).get('data')
    cur = con.execute('INSERT INTO aturan (nama, versi, parameter_json, periode_kalibrasi, dibuat_utc) VALUES (?, ?, ?, ?, ?)',
                      (a.nama, a.versi, a.json(), kal, iso(pd.Timestamp.now(tz='UTC'))))
    aid = cur.lastrowid
    sekarang = iso(pd.Timestamp.now(tz='UTC'))
    for (kode,) in con.execute('SELECT kode FROM stasiun').fetchall():
        con.execute('UPDATE aturan_stasiun SET berlaku_sampai = ? WHERE kode_stasiun = ? AND berlaku_sampai IS NULL '
                    'AND berlaku_mulai < ?', (sekarang, kode, sekarang))
        con.execute('INSERT OR REPLACE INTO aturan_stasiun (kode_stasiun, aturan_id, berlaku_mulai) VALUES (?, ?, ?)',
                    (kode, aid, sekarang))
    con.commit()
    return a, aid
