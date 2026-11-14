"""Dashboard lokal AngkatDulu (tahap 10): server HTTP kecil yang membaca angkatdulu.db dan menyajikan satu halaman.

Hanya mendengar di 127.0.0.1 dan tidak butuh internet (HTML, CSS, JS, grafik SVG semuanya di index.html).
Dipakai oleh demo_bot.py: mesin replay dan bot jalan di thread utama, server ini di thread latar. Server
hanya membaca database (koneksi read-only) dan meneruskan perintah kendali (mulai, jeda, kecepatan).
"""
import json
import math
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import numpy as np
import pandas as pd

from mesin.fitur import seri_layak
from mesin.waktu import SLOT, iso, ke_utc, label_wib, wib

FOLDER = Path(__file__).resolve().parent
NAMA_STASIUN = {'CKRG': 'Karawang', 'BAKO': 'Cibinong', 'CLBG': 'Lembang', 'CJUR': 'Cianjur'}
TIGA_JAM = pd.Timedelta(hours=3)
HARI = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
BULAN = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober',
         'November', 'Desember']


def _tanggal_panjang(t):
    w = wib(t)
    return f'{HARI[w.weekday()]}, {w.day} {BULAN[w.month - 1]} {w.year}'


class Kendali:
    """Keadaan bersama antara loop replay (thread utama) dan permintaan HTTP (thread server).

    fase: MENUNGGU_HP -> PEMANASAN -> SIAP -> BERJALAN -> SELESAI (-> PEMANASAN bila diputar ulang)."""

    KECEPATAN = (0.5, 1.0, 2.0, 3.0, 5.0)        # detik nyata per 30 menit simulasi

    def __init__(self, kode, mulai, selesai, detik_per_tick=2.0, bot=None):
        self.kode = kode; self.mulai = ke_utc(mulai); self.selesai = ke_utc(selesai)
        self.detik_per_tick = float(detik_per_tick); self.bot = bot
        self.fase = 'MENUNGGU_HP'; self.sesi_id = None; self.tau = None; self.jeda = False; self.n_hp = 0
        self.pemanasan_hari = None
        self.minta_mulai = threading.Event()
        self._kunci = threading.Lock()

    def atur(self, **kv):
        with self._kunci:
            for k, v in kv.items():
                setattr(self, k, v)

    def perintah(self, aksi, nilai=None):
        with self._kunci:
            if aksi == 'mulai' and self.fase in ('SIAP', 'SELESAI'):
                self.jeda = False
                self.minta_mulai.set()
            elif aksi == 'jeda' and self.fase == 'BERJALAN':
                self.jeda = True
            elif aksi == 'lanjut':
                self.jeda = False
            elif aksi == 'kecepatan' and nilai is not None:
                try:
                    self.detik_per_tick = min(10.0, max(0.2, float(nilai)))
                except (TypeError, ValueError):
                    pass
        return self.ringkas()

    def ringkas(self):
        tau = self.tau
        return dict(fase=self.fase, jeda=self.jeda, detik_per_tick=self.detik_per_tick, kecepatan=self.KECEPATAN,
                    bot=self.bot, kode=self.kode, n_hp=self.n_hp, sesi_id=self.sesi_id,
                    pemanasan_hari=self.pemanasan_hari,
                    tau=iso(tau) if tau is not None else None,
                    jam=f'{wib(tau):%H.%M}' if tau is not None else None,
                    tanggal=_tanggal_panjang(tau) if tau is not None else None,
                    mulai=iso(self.mulai), selesai=iso(self.selesai),
                    mulai_label=label_wib(self.mulai), selesai_label=label_wib(self.selesai),
                    tanggal_replay=_tanggal_panjang(self.mulai))


# ------------------------------------------------------------------------------------------- data
def _pwv_1jam(con, kode, dari, sampai):
    """PWV rata-rata 1 jam per waktu keputusan tau (akhir slot), sama dengan mesin/fitur.py."""
    df = pd.read_sql_query('SELECT waktu_utc, pwv_mm, flag_kualitas FROM v_pwv_aktif WHERE kode_stasiun = ? '
                           'AND waktu_utc >= ? AND waktu_utc <= ? ORDER BY waktu_utc', con,
                           params=(kode, iso(dari), iso(sampai)))
    if not len(df):
        return pd.Series(dtype=float)
    df['waktu_utc'] = pd.to_datetime(df.waktu_utc, utc=True)
    v = seri_layak(df)
    sebelum = v.shift(1)
    pwv1 = ((v + sebelum) / 2).fillna(v).fillna(sebelum)
    pwv1.index = pwv1.index + SLOT
    return pwv1


def ambang_persentil(pwv1, p, jendela_hari, w0, w1):
    """PWV 1 jam yang harus dilampaui agar persentil >= p, untuk tiap tau di [w0, w1]. Sama dengan
    pipeline/evaluasi/grafik_replay.py (Gambar 3 proposal): referensi = 15 hari sampai 12 jam sebelum tau."""
    out = {}
    for t in pwv1[w0:w1].index:
        ref = pwv1[t - pd.Timedelta(days=jendela_hari):t - pd.Timedelta(hours=12)]
        ref = np.sort(ref[:-1].dropna().to_numpy()) if len(ref) else np.array([])
        out[t] = float(ref[math.ceil(p / 100 * len(ref)) - 1]) if len(ref) else None
    return out


def _bersih(o):
    """NaN/inf -> None supaya JSON valid untuk browser."""
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    if isinstance(o, dict):
        return {k: _bersih(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_bersih(v) for v in o]
    return o


class Penyaji:
    """Menyusun JSON keadaan untuk halaman. Satu koneksi read-only per permintaan."""

    def __init__(self, path_db, kendali, aturan):
        self.uri = Path(path_db).resolve().as_uri() + '?mode=ro'
        self.kendali = kendali; self.aturan = aturan
        self._cache = {}; self._kunci = threading.Lock()

    def _buka(self):
        return sqlite3.connect(self.uri, uri=True, timeout=5)

    def keadaan(self, kode=None):
        with self._kunci:                     # cache dipakai bersama oleh thread permintaan
            return _bersih(self._keadaan(kode))

    def _keadaan(self, kode):
        k = self.kendali
        a = self.aturan
        hasil = dict(kendali=k.ringkas(), stasiun=[], grafik=None, pesan=[], pengguna=None, rekam_jejak=None,
                     aturan=dict(nama=a.nama, versi=a.versi, jam_mulai=a.jam_mulai, jam_selesai=a.jam_selesai,
                                 aman_lagi_sampai=a.aman_lagi_sampai, maks_per_hari=a.maks_per_hari,
                                 l2=a.l2_min, l1=a.l1_min, jendela_hari=a.jendela_hari,
                                 tanya_hujan_menit=a.tanya_hujan_menit))
        sesi = hasil['kendali']['sesi_id']; tau = k.tau
        con = self._buka()
        try:
            for kd, nama, lat, lon in con.execute('SELECT kode, nama, lat, lon FROM stasiun'):
                hasil['stasiun'].append(dict(kode=kd, nama=NAMA_STASIUN.get(kd, nama), lat=lat, lon=lon))
            urut = list(NAMA_STASIUN)
            hasil['stasiun'].sort(key=lambda s: urut.index(s['kode']) if s['kode'] in urut else 99)
            hasil['pengguna'] = self._pengguna(con)
            if sesi is None or tau is None:
                return hasil
            kode = (kode or k.kode).upper()
            if kode not in {s['kode'] for s in hasil['stasiun']}:
                kode = k.kode
            for s in hasil['stasiun']:
                r = con.execute('SELECT level, pwv_1jam_mm, persentil FROM status_stasiun WHERE sesi_id = ? '
                                'AND kode_stasiun = ? AND waktu_utc <= ? ORDER BY waktu_utc DESC LIMIT 1',
                                (sesi, s['kode'], iso(tau))).fetchone()
                if r:
                    s.update(level=r[0], pwv=r[1], persentil=r[2])
            uji = self._uji(con, sesi)
            hasil['grafik'] = self._grafik(con, sesi, kode, tau, uji)
            hasil['pesan'] = self._pesan(con, sesi, tau, uji)
            hasil['rekam_jejak'] = self._rekam_jejak(con, sesi, tau)
        finally:
            con.close()
        return hasil

    # -------------------------------------------------------------------------------- bagian
    def _pengguna(self, con):
        """Titik jemur HP terakhir yang terdaftar di stasiun demo; tanpa HP, titik contoh pengguna uji."""
        sql = ('SELECT l.lat, l.lon, l.kode_stasiun, l.jarak_km FROM lokasi_pengguna l JOIN pengguna u '
               'ON u.id = l.pengguna_id WHERE l.aktif = 1 AND u.aktif = 1 AND u.pengguna_uji = ? '
               'AND l.kode_stasiun = ? ORDER BY l.id DESC LIMIT 1')
        p = con.execute(sql, (0, self.kendali.kode)).fetchone()
        nyata = p is not None
        if p is None:
            p = con.execute(sql, (1, self.kendali.kode)).fetchone()
        return dict(lat=p[0], lon=p[1], kode=p[2], jarak_km=p[3], nyata=nyata) if p else None

    def _uji(self, con, sesi):
        """1 = tampilkan pesan pengguna uji (mode tanpa bot), 0 = pesan HP sungguhan."""
        if self.kendali.bot:
            return 0
        ada = con.execute('SELECT 1 FROM pesan p JOIN pengguna u ON u.id = p.pengguna_id WHERE p.sesi_id = ? '
                          'AND u.pengguna_uji = 0 LIMIT 1', (sesi,)).fetchone()
        return 0 if ada else 1

    def _jendela(self):
        k = self.kendali
        return k.mulai - pd.Timedelta(hours=12), k.selesai

    def _statis(self, con, kode):
        """Bagian yang tetap selama sesi: ambang persentil dan skala sumbu. Dihitung sekali per stasiun."""
        w0, w1 = self._jendela()
        kunci = ('statis', kode, iso(w0), iso(w1))
        if kunci not in self._cache:
            a = self.aturan
            pwv1 = _pwv_1jam(con, kode, w0 - pd.Timedelta(days=a.jendela_hari + 1), w1)
            a2 = ambang_persentil(pwv1, a.l2_min, a.jendela_hari, w0, w1)
            a1 = ambang_persentil(pwv1, a.l1_min, a.jendela_hari, w0, w1) if a.l1_min is not None else {}
            nilai = [v for v in list(pwv1[w0:w1].dropna()) + list(a2.values()) + list(a1.values()) if v is not None]
            lo, hi = (min(nilai), max(nilai)) if nilai else (30.0, 60.0)
            hujan = con.execute('SELECT MAX(hujan_mm_per_jam) FROM observasi_hujan WHERE kode_stasiun = ? '
                                'AND jarak_km = 0 AND waktu_utc >= ? AND waktu_utc < ?',
                                (kode, iso(w0), iso(w1))).fetchone()[0] or 0
            self._cache[kunci] = dict(a2=a2, a1=a1, y=[5 * math.floor((lo - 1) / 5), 5 * math.ceil((hi + 1) / 5)],
                                      y_hujan=max(4, 2 * math.ceil(hujan / 2)))
        return self._cache[kunci]

    def _grafik(self, con, sesi, kode, tau, uji):
        w0, w1 = self._jendela()
        s = self._statis(con, kode)
        st = con.execute('SELECT waktu_utc, pwv_1jam_mm, level, persentil FROM status_stasiun WHERE sesi_id = ? '
                         'AND kode_stasiun = ? AND waktu_utc >= ? AND waktu_utc <= ? ORDER BY waktu_utc',
                         (sesi, kode, iso(w0), iso(tau))).fetchall()
        # Hujan slot [t, t+30 menit) baru diketahui di akhir slot, jadi yang tampil hanya slot yang sudah lewat.
        hujan = con.execute('SELECT waktu_utc, MAX(hujan_mm_per_jam) FROM observasi_hujan WHERE kode_stasiun = ? '
                            'AND jarak_km = 0 AND waktu_utc >= ? AND waktu_utc <= ? GROUP BY waktu_utc '
                            'ORDER BY waktu_utc', (kode, iso(w0), iso(tau - SLOT))).fetchall()
        awal = con.execute('SELECT DISTINCT waktu_utc FROM awal_hujan WHERE kode_stasiun = ? AND waktu_utc >= ? '
                           'AND waktu_utc <= ? ORDER BY waktu_utc', (kode, iso(w0), iso(tau - SLOT))).fetchall()
        tanda = []
        if kode == self.kendali.kode:
            tanda = con.execute(
                "SELECT p.dijadwalkan_utc, p.jenis, p.status, p.alasan FROM pesan p JOIN pengguna u ON "
                "u.id = p.pengguna_id WHERE p.sesi_id = ? AND p.jenis IN ('BERPOTENSI', 'AMAN_LAGI') "
                "AND p.dijadwalkan_utc <= ? AND u.pengguna_uji = ? GROUP BY 1, 2, 3, 4 ORDER BY 1",
                (sesi, iso(tau), uji)).fetchall()
        return dict(
            kode=kode, nama=NAMA_STASIUN.get(kode, kode), w0=iso(w0), w1=iso(w1), tau=iso(tau),
            y=s['y'], y_hujan=s['y_hujan'],
            status=[dict(t=r[0], pwv=r[1], level=r[2], persentil=r[3]) for r in st],
            ambang2=[dict(t=iso(t), v=v) for t, v in s['a2'].items() if t <= tau and v is not None],
            ambang1=[dict(t=iso(t), v=v) for t, v in s['a1'].items() if t <= tau and v is not None],
            hujan=[dict(t=r[0], v=r[1]) for r in hujan if r[1] is not None],
            awal_hujan=[dict(t=r[0], jam=f'{wib(ke_utc(r[0])):%H.%M}') for r in awal],
            tanda=[dict(t=r[0], jam=f'{wib(ke_utc(r[0])):%H.%M}', jenis=r[1], status=r[2], alasan=r[3])
                   for r in tanda])

    def _pesan(self, con, sesi, tau, uji):
        """Pesan sesi ini, satu baris per (waktu, jenis, status) walau ada beberapa HP. Yang terjadwal untuk nanti
        (mis. "Tadi hujan?" 90 menit sesudah peringatan) ikut tampil sebagai terjadwal."""
        baris = con.execute(
            'SELECT MIN(p.id), p.dijadwalkan_utc, p.jenis, p.status, p.alasan, MIN(p.isi), MAX(p.sebagai_notifikasi), '
            'COUNT(*), GROUP_CONCAT(p.id) FROM pesan p JOIN pengguna u ON u.id = p.pengguna_id '
            "WHERE p.sesi_id = ? AND u.pengguna_uji = ? AND (p.dijadwalkan_utc <= ? OR p.status = 'DIJADWALKAN') "
            'GROUP BY p.dijadwalkan_utc, p.jenis, p.status, p.alasan ORDER BY p.dijadwalkan_utc DESC, MIN(p.id) DESC '
            'LIMIT 40', (sesi, uji, iso(tau))).fetchall()
        out = []
        for pid, t, jenis, status, alasan, isi, notif, n, ids in baris:
            ids = [int(x) for x in str(ids).split(',')]
            jawab = con.execute(f"SELECT nilai FROM umpan_balik WHERE pesan_id IN ({','.join('?' * len(ids))}) "
                                'ORDER BY id DESC LIMIT 1', ids).fetchone()
            if isi.startswith('[REPLAY'):
                isi = isi.split('] ', 1)[-1]
            out.append(dict(id=pid, t=t, jam=f'{wib(ke_utc(t)):%H.%M}', jenis=jenis, status=status, alasan=alasan,
                            isi=isi, notifikasi=bool(notif), n_hp=n, jawaban=jawab[0] if jawab else None))
        return out

    def _rekam_jejak(self, con, sesi, tau):
        """Sama dengan Mesin.rekam_jejak tetapi read-only: peringatan BERPOTENSI siang 30 hari terakhir di semua
        stasiun yang dipantau, berapa yang diikuti hujan >= 1 mm/jam dalam 3 jam (hanya hujan sebelum tau)."""
        kunci = ('rj', sesi, iso(tau))
        if kunci in self._cache:
            return self._cache[kunci]
        a = self.aturan
        x = n = 0
        for kode, mulai, diikuti in con.execute(
                "SELECT kode_stasiun, mulai_utc, diikuti_hujan FROM peringatan WHERE sesi_id = ? AND level = "
                "'BERPOTENSI' AND mulai_utc >= ? AND mulai_utc <= ?",
                (sesi, iso(tau - pd.Timedelta(days=30)), iso(tau - TIGA_JAM))).fetchall():
            m = ke_utc(mulai)
            if not (a.jam_mulai <= wib(m).hour < a.jam_selesai):
                continue
            if diikuti is None:
                maks = con.execute('SELECT MAX(hujan_mm_per_jam) FROM observasi_hujan WHERE kode_stasiun = ? '
                                   'AND waktu_utc >= ? AND waktu_utc < ?', (kode, iso(m), iso(m + TIGA_JAM))).fetchone()[0]
                if maks is None:
                    continue
                diikuti = int(maks >= 1.0)
            n += 1; x += int(diikuti)
        n_st = con.execute('SELECT COUNT(DISTINCT kode_stasiun) FROM status_stasiun WHERE sesi_id = ?',
                           (sesi,)).fetchone()[0]
        for k in [k for k in self._cache if k[0] == 'rj']:
            del self._cache[k]
        self._cache[kunci] = dict(x=x, n=n, n_stasiun=n_st)
        return self._cache[kunci]


# ------------------------------------------------------------------------------------------- HTTP
def buat_handler(penyaji):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _kirim(self, kode, isi, jenis='application/json; charset=utf-8'):
            b = isi if isinstance(isi, bytes) else isi.encode('utf-8')
            self.send_response(kode)
            self.send_header('Content-Type', jenis)
            self.send_header('Content-Length', str(len(b)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(b)

        def do_GET(self):
            u = urlsplit(self.path)
            if u.path in ('/', '/index.html'):
                return self._kirim(200, (FOLDER / 'index.html').read_bytes(), 'text/html; charset=utf-8')
            if u.path == '/api/keadaan':
                kode = (parse_qs(u.query).get('kode') or [None])[0]
                try:
                    return self._kirim(200, json.dumps(penyaji.keadaan(kode), allow_nan=False))
                except sqlite3.OperationalError as e:      # database sedang dikunci penulis: halaman mencoba lagi
                    return self._kirim(503, json.dumps({'galat': str(e)}))
            self._kirim(404, json.dumps({'galat': 'tidak ada'}))

        def do_POST(self):
            if urlsplit(self.path).path != '/api/kendali':
                return self._kirim(404, json.dumps({'galat': 'tidak ada'}))
            n = int(self.headers.get('Content-Length', 0) or 0)
            try:
                d = json.loads(self.rfile.read(n) or b'{}')
            except ValueError:
                return self._kirim(400, json.dumps({'galat': 'JSON tidak valid'}))
            self._kirim(200, json.dumps(penyaji.kendali.perintah(d.get('aksi'), d.get('nilai'))))
    return Handler


def jalankan_server(path_db, kendali, aturan, port=8000):
    """Mulai server di thread latar (hanya 127.0.0.1). Kembali (server, url). port=0 memilih port bebas."""
    srv = ThreadingHTTPServer(('127.0.0.1', port), buat_handler(Penyaji(path_db, kendali, aturan)))
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True, name='dasbor').start()
    return srv, f'http://127.0.0.1:{srv.server_address[1]}/'
