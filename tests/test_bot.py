"""Bot Telegram dengan Telegram tiruan: pendaftaran, lokasi demo, pengiriman pesan mesin, jawaban "Tadi hujan?"."""
import pytest
import requests

from bot.layanan import PenanganBot, PengirimTelegram
from bot.telegram import GalatTelegram, Telegram, baca_token
from mesin.waktu import dari_wib
from replay import jalankan

CHAT = 5550001


class TelegramTiruan:
    def __init__(self):
        self.antre = []; self.terkirim = []; self.dijawab = []; self.tombol_dihapus = []; self._id = 100

    def update(self, **isi):
        self.antre.append(dict(update_id=len(self.antre) + 1, **isi))

    def pembaruan(self, offset=None, tunggu=0):
        return [u for u in self.antre if offset is None or u['update_id'] >= offset]

    def kirim(self, chat_id, teks, senyap=False, tombol=None):
        self._id += 1
        self.terkirim.append(dict(chat_id=chat_id, teks=teks, senyap=senyap, tombol=tombol, message_id=self._id))
        return {'message_id': self._id}

    def jawab_tombol(self, callback_id, teks=None):
        self.dijawab.append(callback_id)

    def hapus_tombol(self, chat_id, message_id):
        self.tombol_dihapus.append(message_id)


def pesan_teks(teks, chat=CHAT):
    return dict(message=dict(message_id=1, chat=dict(id=chat, type='private'), **{'from': {'first_name': 'Sri'}},
                             text=teks))


def pesan_lokasi(lat=-6.59, lon=106.80, chat=CHAT):
    return dict(message=dict(message_id=2, chat=dict(id=chat, type='private'), location=dict(latitude=lat, longitude=lon)))


@pytest.fixture(scope='module')
def dbbot(tmp_path_factory):
    from impor import bangun
    from conftest import AKAR
    return bangun(tmp_path_factory.mktemp('dbbot') / 'bot.db', aturan=AKAR / 'config' / 'aturan.yaml')


@pytest.fixture(scope='module')
def demo(dbbot):
    """HP mendaftar, lalu replay 25 Okt 05.00–12.00 WIB dikirim lewat Telegram tiruan."""
    con, aturan, aid = dbbot
    tg = TelegramTiruan()
    pb = PenanganBot(con, tg, stasiun_demo='CKRG', cetak=False)
    tg.update(**pesan_teks('/start')); tg.update(**pesan_lokasi())
    pb.layani()
    m, sesi = jalankan(con, aturan, aid, dari_wib('2026-10-25 05:00'), dari_wib('2026-10-25 12:00'),
                       stasiun=['CKRG'], pemanasan_hari=20, pengirim=PengirimTelegram(con, tg, cetak=False),
                       setelah_tick=lambda m, tau: setattr(pb, 'mesin', m))
    return con, tg, pb, sesi


def test_daftar_dan_lokasi_demo(demo):
    con, tg, pb, sesi = demo
    awal = [k for k in tg.terkirim if k['chat_id'] == CHAT][:2]
    assert 'AngkatDulu' in awal[0]['teks'] and awal[0]['tombol']['keyboard'][0][0]['request_location']
    assert 'Mode demo' in awal[1]['teks'] and 'CKRG' in awal[1]['teks']
    kode, jarak = con.execute('SELECT l.kode_stasiun, l.jarak_km FROM lokasi_pengguna l JOIN pengguna p ON p.id = '
                              'l.pengguna_id WHERE p.telegram_chat_id = ? AND l.aktif = 1', (CHAT,)).fetchone()
    assert kode == 'CKRG' and jarak < 5          # titik contoh, bukan lokasi Bogor yang dikirim HP


def test_pesan_mesin_terkirim_ke_hp(demo):
    con, tg, pb, sesi = demo
    ke_hp = [k for k in tg.terkirim if k['chat_id'] == CHAT][2:]
    assert all(k['chat_id'] > 0 for k in tg.terkirim)             # pengguna uji tidak pernah dikirimi
    jenis = {r[0]: r[1] for r in con.execute(
        'SELECT jenis, telegram_message_id FROM pesan p JOIN pengguna u ON u.id = p.pengguna_id '
        "WHERE p.sesi_id = ? AND u.telegram_chat_id = ? AND p.status = 'TERKIRIM'", (sesi, CHAT))}
    assert {'RINGKASAN_PAGI', 'BERPOTENSI', 'TANYA_HUJAN'} <= set(jenis)
    per_id = {k['message_id']: k for k in ke_hp}
    b = per_id[jenis['BERPOTENSI']]
    assert b['teks'].startswith('[REPLAY · 25 Okt 06.30 WIB]') and 'Berpotensi hujan' in b['teks'] and not b['senyap']
    assert per_id[jenis['RINGKASAN_PAGI']]['senyap']
    t = per_id[jenis['TANYA_HUJAN']]
    assert t['senyap'] and t['tombol']['inline_keyboard'][0][0]['callback_data'].startswith('th:')


def test_jawaban_tadi_hujan_tercatat_sekali(demo):
    con, tg, pb, sesi = demo
    t = [k for k in tg.terkirim if k['tombol'] and 'inline_keyboard' in k['tombol']][-1]
    data = t['tombol']['inline_keyboard'][0][0]['callback_data']          # "Hujan"
    for i in range(2):
        tg.update(callback_query=dict(id=f'cb{i}', data=data,
                                      message=dict(message_id=t['message_id'], chat=dict(id=CHAT, type='private'))))
    pb.layani()
    baris = con.execute("SELECT nilai, peringatan_id FROM umpan_balik WHERE jenis = 'JAWABAN_TADI_HUJAN'").fetchall()
    assert len(baris) == 1 and baris[0][0] == 'YA' and baris[0][1] is not None
    assert tg.dijawab[-2:] == ['cb0', 'cb1'] and t['message_id'] in tg.tombol_dihapus


def test_status_dan_berhenti(demo):
    con, tg, pb, sesi = demo
    tg.update(**pesan_teks('/status')); pb.layani()
    assert tg.terkirim[-1]['teks'].startswith('[REPLAY') and 'CKRG' in tg.terkirim[-1]['teks']
    tg.update(**pesan_teks('/berhenti')); pb.layani()
    n = con.execute('SELECT COUNT(*) FROM v_pelanggan_stasiun v JOIN pengguna p ON p.id = v.pengguna_id '
                    'WHERE p.telegram_chat_id = ?', (CHAT,)).fetchone()[0]
    assert n == 0
    tg.update(**pesan_teks('/start')); pb.layani()                    # bisa mulai lagi
    assert con.execute('SELECT aktif FROM pengguna WHERE telegram_chat_id = ?', (CHAT,)).fetchone()[0] == 1


def test_baca_token(tmp_path):
    f = tmp_path / '.env'
    f.write_text('# komentar\nLAIN=1\nTELEGRAM_BOT_TOKEN = "123:abc"\n', encoding='utf-8')
    assert baca_token(f) == '123:abc'
    f.write_text('TELEGRAM_BOT_TOKEN=\n', encoding='utf-8')
    with pytest.raises(GalatTelegram):
        baca_token(f)
    with pytest.raises(GalatTelegram):
        baca_token(tmp_path / 'tidak_ada.env')


def test_galat_koneksi_tidak_membocorkan_token():
    class SesiPutus:
        def post(self, *a, **k):
            raise requests.ConnectionError('https://api.telegram.org/bot999:RAHASIA/getMe gagal')
    with pytest.raises(GalatTelegram) as e:
        Telegram('999:RAHASIA', sesi=SesiPutus()).saya()
    assert 'RAHASIA' not in str(e.value)


class TelegramPutus(TelegramTiruan):
    """Gagal `n_gagal` kali dengan galat `galat`, lalu normal."""
    def __init__(self, galat, n_gagal=1):
        super().__init__(); self.galat = galat; self.sisa = n_gagal; self.coba = 0

    def kirim(self, chat_id, teks, senyap=False, tombol=None):
        self.coba += 1
        if self.sisa > 0:
            self.sisa -= 1
            raise GalatTelegram(self.galat)
        return super().kirim(chat_id, teks, senyap, tombol)


def test_kirim_ulang_saat_koneksi_putus(demo):
    con = demo[0]
    pid, uid = con.execute("SELECT p.id, p.pengguna_id FROM pesan p JOIN pengguna u ON u.id = p.pengguna_id "
                           "WHERE u.pengguna_uji = 0 AND p.jenis = 'BERPOTENSI'").fetchone()
    pesan = dict(id=pid, pengguna_id=uid, jenis='BERPOTENSI', isi='uji', sebagai_notifikasi=1)
    tg = TelegramPutus('sendMessage: koneksi gagal (ConnectionError)')
    assert PengirimTelegram(con, tg, cetak=False, jeda_ulang=0).kirim(pesan) is not None
    assert tg.coba == 2 and len(tg.terkirim) == 1               # dicoba sekali lagi, terkirim satu kali
    tg = TelegramPutus('sendMessage: koneksi gagal (ConnectionError)', n_gagal=2)
    with pytest.raises(GalatTelegram):                           # tetap gagal: mesin mencatat GAGAL + alasan
        PengirimTelegram(con, tg, cetak=False, jeda_ulang=0).kirim(pesan)
    tg = TelegramPutus('sendMessage: Forbidden: bot was blocked by the user (kode 403)')
    with pytest.raises(GalatTelegram):                           # galat selain koneksi tidak diulang
        PengirimTelegram(con, tg, cetak=False, jeda_ulang=0).kirim(pesan)
    assert tg.coba == 1
