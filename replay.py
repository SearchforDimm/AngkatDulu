"""Putar ulang data historis lewat mesin peringatan (mode replay).

Contoh (waktu dalam WIB):
  python replay.py --mulai "2026-10-27 05:00" --selesai "2026-10-27 20:00" --stasiun CKRG --cetak
  python replay.py --mulai "2026-10-01" --selesai "2026-11-01" --ekspor log_replay

Sebelum `--mulai`, mesin dipanaskan diam-diam (`--pemanasan-hari`, default 30): status dan peringatan
dicatat tanpa pesan, supaya histeresis dan rekam jejak sudah terisi saat replay dimulai.
Database dibangun otomatis dari data/ bila belum ada (lihat db/impor.py).
"""
import argparse
import sys
import time
from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parent
sys.path.insert(0, str(AKAR))
from mesin.basisdata import buka, muat_aturan  # noqa: E402
from mesin.ekspor import ekspor_sesi  # noqa: E402
from mesin.jam import JamReplay  # noqa: E402
from mesin.mesin import Mesin, PengirimLog  # noqa: E402
from mesin.pengguna import PENGGUNA_UJI, buat_pengguna_uji  # noqa: E402
from mesin.periksa import periksa_pelanggaran  # noqa: E402
from mesin.sumber import ReplaySource  # noqa: E402
from mesin.waktu import dari_wib, label_wib  # noqa: E402


def siapkan_db(path, aturan_path):
    if not Path(path).exists():
        sys.path.insert(0, str(AKAR / 'db'))
        from impor import bangun
        con, a, aid = bangun(path, aturan=aturan_path)
        return con, a, aid
    con = buka(path)
    a, aid = muat_aturan(con, aturan_path)
    return con, a, aid


def jalankan(con, aturan, aturan_id, mulai, selesai, stasiun=None, pemanasan_hari=30, detik_per_tick=0.0,
             cetak=False, nama=None, pengirim=None, pantau=None, setelah_tick=None, sebelum_mulai=None):
    """Kembali (mesin, sesi_id). mulai/selesai: Timestamp UTC. stasiun: yang pelanggannya dikirimi pesan;
    pantau: yang statusnya dihitung (default semua stasiun berdata, untuk rekam jejak gabungan).
    sebelum_mulai(mesin): dipanggil sekali sesudah pemanasan, sebelum tick replay pertama (mis. tunggu tombol Mulai).
    setelah_tick(mesin, tau): dipanggil sesudah tiap tick replay (bukan pemanasan), mis. untuk melayani bot."""
    for kode in (stasiun or PENGGUNA_UJI):
        n, la, lo = PENGGUNA_UJI[kode]
        buat_pengguna_uji(con, n, la, lo, kode)
    m = Mesin(con, aturan, aturan_id, ReplaySource(con), pengirim or PengirimLog(cetak=cetak), mode='REPLAY')
    m.buat_sesi(nama or f'replay {label_wib(mulai)} – {label_wib(selesai)}', mulai, selesai, detik_per_tick, stasiun,
                pantau)
    awal_data = min(m.sumber.awal_seri(k) for k in m.stasiun_pantau)
    t = max(mulai - pd.Timedelta(days=pemanasan_hari), awal_data + pd.Timedelta(minutes=30))
    while t < mulai:                                   # pemanasan: status + peringatan, tanpa pesan
        m.tick(t, kirim_pesan=False); t += pd.Timedelta(minutes=30)
    if sebelum_mulai is not None:
        sebelum_mulai(m)
    jam = JamReplay(mulai, selesai, detik_per_tick)
    while (tau := jam.maju()) is not None:
        m.tick(tau)
        if setelah_tick is not None:
            setelah_tick(m, tau)
    m.selesai()
    return m, m.sesi_id


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', default=str(AKAR / 'angkatdulu.db'))
    ap.add_argument('--aturan', default=str(AKAR / 'config' / 'aturan.yaml'))
    ap.add_argument('--mulai', required=True, help='WIB, mis. "2026-10-27 05:00"')
    ap.add_argument('--selesai', required=True, help='WIB')
    ap.add_argument('--stasiun', default=None, help='stasiun yang pelanggannya dikirimi pesan, mis. CKRG atau CKRG,BAKO '
                    '(default: semua yang punya pelanggan). Status semua stasiun berdata tetap dihitung.')
    ap.add_argument('--pemanasan-hari', type=float, default=30)
    ap.add_argument('--detik-per-tick', type=float, default=0.0, help='0 = secepatnya')
    ap.add_argument('--cetak', action='store_true', help='cetak pesan saat terkirim')
    ap.add_argument('--ekspor', default=None, help='folder untuk CSV status, peringatan, pesan')
    x = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')    # konsol Windows
    except Exception:
        pass

    con, aturan, aid = siapkan_db(x.db, x.aturan)
    stasiun = x.stasiun.upper().split(',') if x.stasiun else None
    t0 = time.time()
    m, sesi = jalankan(con, aturan, aid, dari_wib(x.mulai), dari_wib(x.selesai), stasiun, x.pemanasan_hari,
                       x.detik_per_tick, x.cetak)
    print(f'\nSesi {sesi}: aturan {aturan.nama} {aturan.versi}, pesan untuk {", ".join(m.daftar_stasiun)}, '
          f'dipantau {", ".join(m.stasiun_pantau)}, {time.time() - t0:.1f} detik')
    for jenis, status, n in con.execute('SELECT jenis, status, COUNT(*) FROM pesan WHERE sesi_id = ? GROUP BY 1, 2 '
                                        'ORDER BY 1, 2', (sesi,)):
        print(f'  {jenis:15s} {status:11s} {n}')
    salah = periksa_pelanggaran(con, sesi, aturan)
    print('Pelanggaran kebijakan pesan:', len(salah))
    for s in salah[:20]:
        print('  -', s)
    if x.ekspor:
        for nama, path in ekspor_sesi(con, sesi, x.ekspor).items():
            print(f'  ekspor {nama}: {path}')


if __name__ == '__main__':
    main()
