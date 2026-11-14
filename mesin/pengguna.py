"""Pengguna dan lokasi: cari stasiun SEHAT terdekat (FR-07) dan buat pengguna uji untuk replay."""
import math

import pandas as pd

from .waktu import iso


def jarak_km(lat1, lon1, lat2, lon2):
    r = 6371.0; p = math.radians
    a = math.sin(p(lat2 - lat1) / 2) ** 2 + math.cos(p(lat1)) * math.cos(p(lat2)) * math.sin(p(lon2 - lon1) / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def stasiun_terdekat(con, lat, lon):
    """(kode, nama, jarak_km) stasiun SEHAT terdekat yang punya data PWV."""
    baris = con.execute("SELECT kode, nama, lat, lon FROM stasiun WHERE status = 'SEHAT' "
                        'AND kode IN (SELECT DISTINCT kode_stasiun FROM observasi_pwv)').fetchall()
    return min(((k, n, jarak_km(lat, lon, la, lo)) for k, n, la, lo in baris), key=lambda x: x[2])


def simpan_lokasi(con, pengguna_id, lat, lon, kode=None):
    """Simpan lokasi (dibulatkan 3 desimal, ±100 m) dan nonaktifkan lokasi lama. Kembali (kode, nama, jarak)."""
    lat, lon = round(lat, 3), round(lon, 3)
    if kode is None:
        kode, nama, jarak = stasiun_terdekat(con, lat, lon)
    else:
        nama, la, lo = con.execute('SELECT nama, lat, lon FROM stasiun WHERE kode = ?', (kode,)).fetchone()
        jarak = jarak_km(lat, lon, la, lo)
    con.execute('UPDATE lokasi_pengguna SET aktif = 0 WHERE pengguna_id = ? AND aktif = 1', (pengguna_id,))
    con.execute('INSERT INTO lokasi_pengguna (pengguna_id, lat, lon, kode_stasiun, jarak_km, aktif, dibuat_utc) '
                'VALUES (?, ?, ?, ?, ?, 1, ?)', (pengguna_id, lat, lon, kode, round(jarak, 1), iso(pd.Timestamp.now(tz='UTC'))))
    return kode, nama, jarak


def buat_pengguna_uji(con, nama, lat, lon, kode=None):
    """Pengguna uji untuk replay (chat_id negatif, tidak pernah dikirimi Telegram sungguhan)."""
    ada = con.execute('SELECT id FROM pengguna WHERE nama_tampilan = ? AND pengguna_uji = 1', (nama,)).fetchone()
    if ada:
        return ada[0]
    chat = -1 - con.execute('SELECT COUNT(*) FROM pengguna WHERE pengguna_uji = 1').fetchone()[0]
    cur = con.execute("INSERT INTO pengguna (telegram_chat_id, jenis_chat, nama_tampilan, peran, pengguna_uji, aktif, "
                      "bergabung_utc) VALUES (?, 'PRIBADI', ?, 'PETANI', 1, 1, ?)",
                      (chat, nama, iso(pd.Timestamp.now(tz='UTC'))))
    simpan_lokasi(con, cur.lastrowid, lat, lon, kode)
    con.commit()
    return cur.lastrowid


# Satu pengguna uji per stasiun, ±3 km dari stasiun (titik jemur fiktif, bukan alamat orang sungguhan).
PENGGUNA_UJI = {
    'CKRG': ('Bu Sri (uji)', -6.130, 107.310),
    'BAKO': ('Uji BAKO', -6.510, 106.830),
    'CLBG': ('Uji CLBG', -6.840, 107.600),
    'CJUR': ('Uji CJUR', -6.840, 107.120),
}
