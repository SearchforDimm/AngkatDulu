"""Layanan bot AngkatDulu: menangani pesan masuk (pendaftaran, lokasi, jawaban "Tadi hujan?") dan mengirim
pesan yang dijadwalkan mesin ke Telegram.

Logika peringatan dan kebijakan pesan tetap di `mesin/`; modul ini hanya penghubung.
"""
import time

import pandas as pd

from bot.telegram import GalatTelegram
from mesin import template as T
from mesin.pengguna import PENGGUNA_UJI, simpan_lokasi
from mesin.waktu import iso

PERINTAH = [('start', 'Mulai dan daftarkan lokasi jemur'),
            ('status', 'Status stasiun terdekat saat ini'),
            ('berhenti', 'Berhenti menerima peringatan')]

TOMBOL_LOKASI = {'keyboard': [[{'text': 'Kirim lokasi jemur', 'request_location': True}]],
                 'resize_keyboard': True, 'one_time_keyboard': True}
JAWABAN = {'Y': ('YA', 'Hujan'), 'T': ('TIDAK', 'Tidak hujan'), 'X': (None, 'Tidak tahu')}


def tombol_tanya_hujan(pesan_id):
    return {'inline_keyboard': [[{'text': teks, 'callback_data': f'th:{pesan_id}:{k}'}
                                 for k, (_, teks) in JAWABAN.items()]]}


class PengirimTelegram:
    """Pengganti PengirimLog: pesan jatuh tempo dikirim ke chat Telegram pengguna sungguhan.
    Pengguna uji (chat_id negatif) tidak dikirimi apa pun."""

    def __init__(self, con, tg, cetak=True, jeda_ulang=1.0):
        self.con = con; self.tg = tg; self.cetak = cetak; self.jeda_ulang = jeda_ulang

    def kirim(self, pesan):
        """Kirim satu pesan. Gangguan koneksi dicoba sekali lagi (pesan peringatan yang hilang lebih buruk daripada
        pesan dobel); galat lain (mis. bot diblokir) langsung diteruskan, dan mesin mencatatnya GAGAL beserta alasan."""
        baris = self.con.execute('SELECT telegram_chat_id, pengguna_uji FROM pengguna WHERE id = ?',
                                 (pesan['pengguna_id'],)).fetchone()
        if baris is None or baris[1] == 1:
            return None
        tombol = tombol_tanya_hujan(pesan['id']) if pesan['jenis'] == 'TANYA_HUJAN' else None
        for coba in (1, 2):
            try:
                hasil = self.tg.kirim(baris[0], pesan['isi'], senyap=not pesan['sebagai_notifikasi'], tombol=tombol)
                break
            except GalatTelegram as e:
                if coba == 1 and 'koneksi gagal' in str(e):
                    if self.cetak:
                        print(f"  ! {pesan['jenis']}: {e}; mencoba lagi", flush=True)
                    time.sleep(self.jeda_ulang)
                    if hasattr(self.tg, 'segarkan'):
                        self.tg.segarkan()               # koneksi baru untuk percobaan kedua
                    continue
                if self.cetak:
                    print(f"  ! Telegram GAGAL {pesan['jenis']} ke chat {baris[0]}: {e}", flush=True)
                raise
        if self.cetak:
            bunyi = 'notif' if pesan['sebagai_notifikasi'] else 'senyap'
            print(f"  -> Telegram ({bunyi}) {pesan['jenis']}: {pesan['isi'][:90]}", flush=True)
        return hasil.get('message_id')


class PenanganBot:
    """Menangani update Telegram. `stasiun_demo`: bila diisi (mis. 'CKRG'), lokasi yang dikirim pengguna diganti
    titik jemur contoh di dekat stasiun itu, supaya demo di Bogor tetap memakai data Karawang. `mesin` dan `waktu`
    (fungsi -> Timestamp UTC) dipakai untuk status terkini dan waktu umpan balik dalam mode replay."""

    def __init__(self, con, tg, stasiun_demo=None, mesin=None, waktu=None, cetak=True):
        self.con = con; self.tg = tg; self.stasiun_demo = stasiun_demo
        self.mesin = mesin; self.waktu = waktu or (lambda: pd.Timestamp.now(tz='UTC')); self.cetak = cetak
        self.offset = None

    # ---------------------------------------------------------------- loop
    def layani(self, tunggu=0):
        """Ambil dan tangani semua update yang ada (long polling `tunggu` detik). Kembali jumlah update."""
        updates = self.tg.pembaruan(self.offset, tunggu)
        for u in updates:
            self.offset = u['update_id'] + 1
            try:
                self.tangani(u)
            except Exception as e:          # satu update rusak tidak boleh menghentikan bot
                print(f'  ! gagal menangani update {u.get("update_id")}: {e}', flush=True)
        if updates:
            self.con.commit()
        return len(updates)

    def tangani(self, u):
        if 'callback_query' in u:
            return self._tombol(u['callback_query'])
        m = u.get('message')
        if not m:
            return
        chat = m['chat']
        if 'location' in m:
            return self._lokasi(chat, m['location'])
        teks = (m.get('text') or '').strip()
        perintah = teks.split()[0].split('@')[0].lower() if teks.startswith('/') else ''
        if perintah == '/start':
            return self._mulai(chat, m.get('from', {}))
        if perintah == '/status':
            return self._status(chat)
        if perintah == '/berhenti':
            return self._berhenti(chat)
        self.tg.kirim(chat['id'], 'Ketik /start untuk mendaftar, /status untuk melihat status, '
                                  'atau /berhenti untuk berhenti.')

    # ---------------------------------------------------------------- perintah
    def _pengguna(self, chat_id):
        return self.con.execute('SELECT id, aktif FROM pengguna WHERE telegram_chat_id = ?', (chat_id,)).fetchone()

    def _mulai(self, chat, dari):
        ada = self._pengguna(chat['id'])
        if ada:
            self.con.execute('UPDATE pengguna SET aktif = 1, berhenti_utc = NULL WHERE id = ?', (ada[0],))
        else:
            jenis = 'GRUP' if chat.get('type') in ('group', 'supergroup') else 'PRIBADI'
            nama = dari.get('first_name') or chat.get('title') or 'Pengguna'
            self.con.execute("INSERT INTO pengguna (telegram_chat_id, jenis_chat, nama_tampilan, peran, pengguna_uji, "
                             "aktif, bergabung_utc) VALUES (?, ?, ?, 'PETANI', 0, 1, ?)",
                             (chat['id'], jenis, nama, iso(pd.Timestamp.now(tz='UTC'))))
        self.con.commit()
        self._log(f'/start dari chat {chat["id"]}')
        self.tg.kirim(chat['id'], T.sambutan(), tombol=TOMBOL_LOKASI)

    def _lokasi(self, chat, lokasi):
        p = self._pengguna(chat['id'])
        if p is None:
            self._mulai(chat, {}); p = self._pengguna(chat['id'])
        if self.stasiun_demo:
            _, lat, lon = PENGGUNA_UJI[self.stasiun_demo]
            kode, nama, jarak = simpan_lokasi(self.con, p[0], lat, lon, self.stasiun_demo)
            awal = ('Mode demo: titik jemur diatur ke contoh di dekat stasiun '
                    f'{kode}, bukan lokasi Anda sebenarnya. ')
        else:
            kode, nama, jarak = simpan_lokasi(self.con, p[0], lokasi['latitude'], lokasi['longitude'])
            awal = ''
        self.con.commit()
        self._log(f'lokasi chat {chat["id"]} -> {kode} ±{jarak:.0f} km')
        self.tg.kirim(chat['id'], awal + T.info_jarak(kode, nama, jarak) + ' ' + T.kondisi_awal(self._level(kode)),
                      tombol={'remove_keyboard': True})

    def _status(self, chat):
        r = self.con.execute('SELECT l.kode_stasiun, l.jarak_km FROM lokasi_pengguna l JOIN pengguna p '
                             'ON p.id = l.pengguna_id WHERE p.telegram_chat_id = ? AND l.aktif = 1 AND p.aktif = 1',
                             (chat['id'],)).fetchone()
        if r is None:
            return self.tg.kirim(chat['id'], 'Anda belum terdaftar. Ketik /start lalu kirim lokasi jemur.')
        kode, jarak = r
        pwv = None
        if self.mesin is not None:
            pwv = (self.mesin._fitur.get(kode) or {}).get('pwv_1jam')
        teks = f'Stasiun {kode} (±{jarak:.0f} km): {T.STATUS_TEKS[self._level(kode)]}.'
        if pwv is not None and pwv == pwv:
            teks += f' Uap air 1 jam terakhir {pwv:.0f} mm.'
        if self.mesin is not None and self.mesin.mode == 'REPLAY':
            teks = T.label(self.waktu(), 'REPLAY') + teks
        self.tg.kirim(chat['id'], teks)

    def _berhenti(self, chat):
        p = self._pengguna(chat['id'])
        if p:
            self.con.execute('UPDATE pengguna SET aktif = 0, berhenti_utc = ? WHERE id = ?',
                             (iso(pd.Timestamp.now(tz='UTC')), p[0]))
            self.con.commit()
        self.tg.kirim(chat['id'], 'Peringatan dihentikan. Ketik /start kapan saja untuk mulai lagi.')

    def _tombol(self, cq):
        data = cq.get('data') or ''
        chat_id = cq['message']['chat']['id']
        bagian = data.split(':')
        if len(bagian) != 3 or bagian[0] != 'th' or bagian[2] not in JAWABAN:
            return self.tg.jawab_tombol(cq['id'])
        pesan_id, kode = int(bagian[1]), bagian[2]
        nilai, teks = JAWABAN[kode]
        p = self._pengguna(chat_id)
        baris = self.con.execute('SELECT peringatan_id FROM pesan WHERE id = ? AND pengguna_id = ?',
                                 (pesan_id, p[0] if p else -1)).fetchone()
        if baris is not None and nilai is not None:
            sudah = self.con.execute("SELECT 1 FROM umpan_balik WHERE pesan_id = ? AND jenis = 'JAWABAN_TADI_HUJAN'",
                                     (pesan_id,)).fetchone()
            if not sudah:
                self.con.execute("INSERT INTO umpan_balik (pengguna_id, pesan_id, peringatan_id, jenis, nilai, waktu_utc) "
                                 "VALUES (?, ?, ?, 'JAWABAN_TADI_HUJAN', ?, ?)",
                                 (p[0], pesan_id, baris[0], nilai, iso(self.waktu())))
                self.con.commit()
        self._log(f'jawaban "Tadi hujan?" chat {chat_id}: {teks}')
        self.tg.jawab_tombol(cq['id'], 'Tercatat')
        try:
            self.tg.hapus_tombol(chat_id, cq['message']['message_id'])
        except Exception:
            pass
        balas = T.terima_laporan() if nilai else 'Baik, terima kasih.'
        self.tg.kirim(chat_id, f'{balas} (Jawaban: {teks})', senyap=True)

    # ---------------------------------------------------------------- bantuan
    def _level(self, kode):
        if self.mesin is not None and kode in self.mesin.penilai:
            return self.mesin.penilai[kode].level
        return 'AMAN'

    def _log(self, s):
        if self.cetak:
            print(f'  [bot] {s}', flush=True)
