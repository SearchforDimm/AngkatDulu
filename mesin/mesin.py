"""Mesin peringatan AngkatDulu: satu tick per 30 menit waktu simulasi (PRD 10.3).

setiap tick tau:
  untuk tiap stasiun yang punya data (dipantau semua, supaya rekam jejak bisa digabung):
      data  = sumber.ambil(stasiun, sampai=tau)        # hanya slot yang sudah selesai
      fitur = hitung_fitur(data) di slot terakhir
      level = penilai.nilai(fitur)                     # histeresis 60 menit, TANPA_DATA setelah 2 jam
      simpan status_stasiun
      bila level berubah: tutup/buka peringatan; bila stasiun punya pelanggan: rencanakan pesan (kebijakan 8.4)
  penjadwal: ringkasan pagi 06.00 WIB; TANYA_HUJAN sudah dijadwalkan +90 menit
  pengirim: kirim pesan yang jatuh tempo
"""
import math

import pandas as pd

from . import template as T
from .aturan import PenilaiAturan
from .fitur import hitung_fitur
from .kebijakan import putuskan, transisi
from .waktu import SLOT, iso, ke_utc, tanggal_wib, wib

HARI = pd.Timedelta(days=1)
TIGA_JAM = pd.Timedelta(hours=3)


def _angka(x):
    if x is None:
        return None
    x = float(x)
    return None if math.isnan(x) else x


class PengirimLog:
    """Pengirim tiruan untuk replay: pesan jatuh tempo ditandai TERKIRIM. Bot Telegram mengganti `kirim`."""
    def __init__(self, cetak=False):
        self.cetak = cetak

    def kirim(self, pesan):
        if self.cetak:
            bunyi = '(notif)' if pesan['sebagai_notifikasi'] else '(senyap)'
            print(f"{bunyi} [{pesan['jenis']}] ke pengguna {pesan['pengguna_id']}: {pesan['isi']}", flush=True)
        return None          # telegram_message_id


class Mesin:
    def __init__(self, con, aturan, aturan_id, sumber, pengirim=None, mode='REPLAY'):
        self.con = con; self.aturan = aturan; self.aturan_id = aturan_id
        self.sumber = sumber; self.pengirim = pengirim or PengirimLog(); self.mode = mode
        self.sesi_id = None; self.daftar_stasiun = []; self.stasiun_pantau = []
        self.penilai = {}; self._fitur = {}; self._episode_berpotensi = {}

    # ------------------------------------------------------------ sesi
    def buat_sesi(self, nama, mulai, selesai, detik_per_tick=0.0, stasiun=None, pantau=None):
        """stasiun: stasiun yang pelanggannya dikirimi pesan (default: semua yang punya pelanggan).
        pantau: stasiun yang statusnya dihitung (default: semua yang punya data), untuk rekam jejak gabungan."""
        cur = self.con.execute(
            'INSERT INTO sesi_replay (nama, mode, periode_mulai, periode_selesai, detik_per_tick, status, dimulai_nyata) '
            "VALUES (?, ?, ?, ?, ?, 'BERJALAN', ?)",
            (nama, self.mode, iso(mulai), iso(selesai), detik_per_tick, iso(pd.Timestamp.now(tz='UTC'))))
        self.sesi_id = cur.lastrowid
        self.daftar_stasiun = list(stasiun or self.stasiun_berpelanggan())
        pantau = self.sumber.daftar_stasiun() if pantau is None else pantau
        self.stasiun_pantau = sorted(set(self.daftar_stasiun) | set(pantau))
        self.penilai = {k: PenilaiAturan(self.aturan) for k in self.stasiun_pantau}
        self.con.commit()
        return self.sesi_id

    def selesai(self):
        self.con.execute("UPDATE sesi_replay SET status = 'SELESAI' WHERE id = ?", (self.sesi_id,))
        self.con.commit()

    def stasiun_berpelanggan(self):
        return [r[0] for r in self.con.execute(
            'SELECT DISTINCT kode_stasiun FROM v_pelanggan_stasiun ORDER BY kode_stasiun')]

    def pelanggan(self, kode):
        return self.con.execute('SELECT pengguna_id, jarak_km FROM v_pelanggan_stasiun WHERE kode_stasiun = ? '
                                'ORDER BY pengguna_id', (kode,)).fetchall()

    # ------------------------------------------------------------ fitur
    def fitur_saat(self, kode, tau):
        a = self.aturan
        sejak = (tau - SLOT).floor('D') - (a.jendela_hari + 1) * HARI
        v = self.sumber.ambil(kode, tau, sejak=sejak)
        if len(v) == 0 or v.index[-1] != tau - SLOT:
            return None
        f = hitung_fitur(v, a.jendela_hari, a.min_hari, awal_seri=self.sumber.awal_seri(kode),
                         reset=a.reset.get(kode), hanya_akhir=True)
        return f.iloc[-1].to_dict()

    # ------------------------------------------------------------ tick
    def tick(self, tau, kirim_pesan=True):
        tau = ke_utc(tau)
        for kode in self.stasiun_pantau:
            f = self.fitur_saat(kode, tau)
            p = self.penilai[kode]; sebelum = p.level; level = p.nilai(f)
            self._fitur[kode] = f
            f = f or {}
            self.con.execute(
                'INSERT INTO status_stasiun (sesi_id, kode_stasiun, waktu_utc, aturan_id, pwv_1jam_mm, anomali_mm, '
                'persentil, delta_3jam_mm, level) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (self.sesi_id, kode, iso(tau), self.aturan_id, _angka(f.get('pwv_1jam')), _angka(f.get('anomali')),
                 _angka(f.get('persentil')), _angka(f.get('delta_3j')), level))
            if level != sebelum:
                self._ganti_level(kode, sebelum, level, tau, f, kirim_pesan)
        if kirim_pesan:
            self._penjadwal(tau)
            self._kirim_jatuh_tempo(tau)
        self.con.execute('UPDATE sesi_replay SET waktu_simulasi = ? WHERE id = ?', (iso(tau), self.sesi_id))
        self.con.commit()

    def _ganti_level(self, kode, sebelum, level, tau, f, kirim_pesan):
        cur = self.con.cursor()
        cur.execute('UPDATE peringatan SET selesai_utc = ? WHERE sesi_id = ? AND kode_stasiun = ? AND selesai_utc IS NULL',
                    (iso(tau), self.sesi_id, kode))
        if level in ('WASPADA', 'BERPOTENSI'):
            cur.execute('INSERT INTO peringatan (sesi_id, kode_stasiun, aturan_id, level, mulai_utc, pwv_pemicu_mm) '
                        'VALUES (?, ?, ?, ?, ?, ?)',
                        (self.sesi_id, kode, self.aturan_id, level, iso(tau), _angka(f.get('pwv_1jam'))))
            if level == 'BERPOTENSI':
                self._episode_berpotensi[kode] = cur.lastrowid
        jenis = transisi(sebelum, level)
        if jenis and kirim_pesan and kode in self.daftar_stasiun:
            pid = self._episode_berpotensi.get(kode)
            for pengguna_id, jarak in self.pelanggan(kode):
                self._rencanakan(jenis, pengguna_id, kode, jarak, tau, level, pid)

    # ------------------------------------------------------------ perencana pesan
    def _kuota(self, pengguna_id, tau):
        hari = str(tanggal_wib(tau))
        n, b = self.con.execute(
            "SELECT COUNT(*), COALESCE(SUM(jenis = 'BERPOTENSI'), 0) FROM pesan WHERE pengguna_id = ? AND sesi_id = ? "
            "AND jenis IN ('BERPOTENSI', 'AMAN_LAGI') AND status IN ('DIJADWALKAN', 'TERKIRIM') "
            "AND date(datetime(dijadwalkan_utc, '+7 hours')) = ?", (pengguna_id, self.sesi_id, hari)).fetchone()
        return n, b > 0

    def _simpan_pesan(self, pengguna_id, jenis, isi, tau, status, alasan=None, peringatan_id=None, notifikasi=1):
        self.con.execute(
            'INSERT INTO pesan (pengguna_id, sesi_id, peringatan_id, jenis, sebagai_notifikasi, isi, dijadwalkan_utc, '
            'status, alasan) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (pengguna_id, self.sesi_id, peringatan_id, jenis, notifikasi, T.label(tau, self.mode) + isi, iso(tau),
             status, alasan))

    def _rencanakan(self, jenis, pengguna_id, kode, jarak, tau, level, peringatan_id):
        n, ada_b = self._kuota(pengguna_id, tau)
        hasil = putuskan(jenis, tau, n, ada_b, self.aturan)
        if hasil is None:
            return
        status, alasan = hasil
        if jenis == 'BERPOTENSI':
            isi = T.berpotensi(kode, jarak, T.rekam_jejak(*self.rekam_jejak(tau), len(self.stasiun_pantau)))
        else:
            isi = T.aman_lagi(level, kode, jarak)
        self._simpan_pesan(pengguna_id, jenis, isi, tau, status, alasan, peringatan_id)
        if jenis == 'BERPOTENSI' and status == 'DIJADWALKAN':
            t2 = tau + pd.Timedelta(minutes=self.aturan.tanya_hujan_menit)
            self._simpan_pesan(pengguna_id, 'TANYA_HUJAN', T.tanya_hujan(), t2, 'DIJADWALKAN', None, peringatan_id, 0)

    def rekam_jejak(self, tau):
        """(x, n): dari peringatan BERPOTENSI siang (mulai 06.00–18.00 WIB, yaitu yang setara notifikasi) 30 hari
        terakhir di SEMUA stasiun yang dipantau sesi ini, berapa yang diikuti hujan >= 1 mm/jam dalam 3 jam di stasiun
        itu. Hanya memakai hujan yang sudah terjadi sebelum tau. Digabung karena satu stasiun saja terlalu sedikit
        kejadiannya (CKRG Sep–Okt: 1 dari 26). Ini ketepatan per peringatan, berbeda dari 'peringatan tepat' di
        evaluasi (per slot 30 menit saat status menyala)."""
        terbuka = self.con.execute(
            "SELECT id, kode_stasiun, mulai_utc FROM peringatan WHERE sesi_id = ? AND level = 'BERPOTENSI' "
            'AND diikuti_hujan IS NULL AND mulai_utc <= ?', (self.sesi_id, iso(tau - TIGA_JAM))).fetchall()
        for pid, kode, mulai in terbuka:
            m = ke_utc(mulai)
            maks = self.con.execute(
                'SELECT MAX(hujan_mm_per_jam) FROM observasi_hujan WHERE kode_stasiun = ? AND waktu_utc >= ? AND waktu_utc < ?',
                (kode, iso(m), iso(m + TIGA_JAM))).fetchone()[0]
            if maks is not None:
                self.con.execute('UPDATE peringatan SET diikuti_hujan = ? WHERE id = ?', (int(maks >= 1.0), pid))
        x, n = self.con.execute(
            "SELECT COALESCE(SUM(diikuti_hujan), 0), COUNT(*) FROM peringatan WHERE sesi_id = ? "
            "AND level = 'BERPOTENSI' AND diikuti_hujan IS NOT NULL AND mulai_utc >= ? "
            "AND CAST(strftime('%H', datetime(mulai_utc, '+7 hours')) AS INTEGER) >= ? "
            "AND CAST(strftime('%H', datetime(mulai_utc, '+7 hours')) AS INTEGER) < ?",
            (self.sesi_id, iso(tau - 30 * HARI), int(self.aturan.jam_mulai), int(self.aturan.jam_selesai))).fetchone()
        return int(x), int(n)

    # ------------------------------------------------------------ penjadwal
    def _tren_24jam(self, kode, tau):
        now = (self._fitur.get(kode) or {}).get('pwv_1jam')
        v = self.sumber.ambil(kode, tau - HARI, sejak=tau - HARI - pd.Timedelta(hours=1))
        lalu = v.iloc[-2:].mean() if len(v) else float('nan')
        if now is None or math.isnan(now) or math.isnan(lalu):
            return None
        d = now - lalu
        return 'naik' if d >= 3 else ('turun' if d <= -3 else 'stabil')

    def _penjadwal(self, tau):
        w = wib(tau)
        if (w.hour, w.minute) != (6, 0):
            return
        for kode in self.daftar_stasiun:
            level = self.penilai[kode].level; tren = self._tren_24jam(kode, tau)
            for pengguna_id, jarak in self.pelanggan(kode):
                self._simpan_pesan(pengguna_id, 'RINGKASAN_PAGI', T.ringkasan_pagi(tren, level, kode, jarak), tau,
                                   'DIJADWALKAN', notifikasi=0)

    # ------------------------------------------------------------ pengirim
    def _kirim_jatuh_tempo(self, tau):
        cur = self.con.execute(
            "SELECT id, pengguna_id, jenis, isi, sebagai_notifikasi FROM pesan WHERE sesi_id = ? AND status = 'DIJADWALKAN' "
            'AND dijadwalkan_utc <= ? ORDER BY dijadwalkan_utc, id', (self.sesi_id, iso(tau)))
        for pid, pengguna_id, jenis, isi, notif in cur.fetchall():
            pesan = dict(id=pid, pengguna_id=pengguna_id, jenis=jenis, isi=isi, sebagai_notifikasi=notif)
            try:
                mid = self.pengirim.kirim(pesan)
                self.con.execute("UPDATE pesan SET status = 'TERKIRIM', terkirim_utc = ?, terkirim_nyata = ?, "
                                 'telegram_message_id = ? WHERE id = ?',
                                 (iso(tau), iso(pd.Timestamp.now(tz='UTC')), mid, pid))
            except Exception as e:          # mesin tetap jalan walau pengiriman gagal
                self.con.execute("UPDATE pesan SET status = 'GAGAL', alasan = ? WHERE id = ?", (str(e)[:200], pid))
