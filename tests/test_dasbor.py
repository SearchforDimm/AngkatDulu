"""Dashboard lokal (dasbor/): isi JSON sesuai mesin, endpoint HTTP, dan kendali replay."""
import json
import urllib.error
import urllib.request

import pytest

from bot.layanan import PenanganBot, PengirimTelegram
from dasbor.server import Kendali, Penyaji, jalankan_server
from mesin.waktu import SLOT, dari_wib, iso
from replay import jalankan
from test_bot import TelegramTiruan, pesan_lokasi, pesan_teks

MULAI, SELESAI = dari_wib('2026-10-25 05:00'), dari_wib('2026-10-25 09:00')
TAU = dari_wib('2026-10-25 08:30')


@pytest.fixture(scope='module')
def sesi(tmp_path_factory):
    """HP terdaftar lewat Telegram tiruan, lalu replay 25 Okt 05.00–09.00 WIB; dashboard membaca hasilnya."""
    from conftest import AKAR
    from impor import bangun
    path = tmp_path_factory.mktemp('dasbor') / 'dasbor.db'
    con, aturan, aid = bangun(path, aturan=AKAR / 'config' / 'aturan.yaml')
    tg = TelegramTiruan()
    pb = PenanganBot(con, tg, stasiun_demo='CKRG', cetak=False)
    tg.update(**pesan_teks('/start')); tg.update(**pesan_lokasi())
    pb.layani()
    dipanggil = []
    m, sid = jalankan(con, aturan, aid, MULAI, SELESAI, stasiun=['CKRG'], pemanasan_hari=20,
                      pengirim=PengirimTelegram(con, tg, cetak=False),
                      sebelum_mulai=lambda m: dipanggil.append(('sebelum', m.sesi_id)),
                      setelah_tick=lambda m, tau: dipanggil.append(('tick', tau)))
    k = Kendali('CKRG', MULAI, SELESAI, 2.0, bot='angkatdulu_uji_bot')
    k.atur(fase='BERJALAN', sesi_id=sid, tau=TAU)
    return dict(path=path, con=con, aturan=aturan, sid=sid, kendali=k, dipanggil=dipanggil,
                penyaji=Penyaji(path, k, aturan))


def test_sebelum_mulai_dipanggil_sekali_sebelum_tick_pertama(sesi):
    d = sesi['dipanggil']
    assert d[0] == ('sebelum', sesi['sid'])
    assert [x for x in d if x[0] == 'sebelum'] == [d[0]]
    assert d[1] == ('tick', MULAI)


def test_keadaan_sesuai_mesin(sesi):
    d = sesi['penyaji'].keadaan()
    json.dumps(d, allow_nan=False)                                   # JSON valid untuk browser
    assert {s['kode'] for s in d['stasiun']} == {'CKRG', 'BAKO', 'CLBG', 'CJUR'}
    assert all(s.get('level') in ('AMAN', 'WASPADA', 'BERPOTENSI', 'TANPA_DATA') for s in d['stasiun'])
    g = d['grafik']
    assert g['kode'] == 'CKRG' and g['status'][-1]['t'] == iso(TAU)
    assert g['status'][0]['t'] >= g['w0']                            # 12 jam sebelum replay, dari pemanasan
    assert all(h['t'] <= iso(TAU - SLOT) for h in g['hujan'])       # hujan hanya yang sudah lewat
    assert d['pengguna']['nyata'] and d['pengguna']['kode'] == 'CKRG' and d['pengguna']['jarak_km'] < 5


def test_garis_ambang_sama_dengan_keputusan_persentil(sesi):
    """Garis 'batas berpotensi' di grafik harus tepat di batas yang dipakai mesin: PWV >= batas <=> persentil >= 80."""
    g = sesi['penyaji'].keadaan()['grafik']
    a2 = {x['t']: x['v'] for x in g['ambang2']}; a1 = {x['t']: x['v'] for x in g['ambang1']}
    dicek = 0
    for s in g['status']:
        if s['pwv'] is None or s['persentil'] is None or s['t'] not in a2:
            continue
        assert (s['persentil'] >= 80) == (s['pwv'] >= a2[s['t']] - 1e-9), s
        assert (s['persentil'] >= 65) == (s['pwv'] >= a1[s['t']] - 1e-9), s
        dicek += 1
    assert dicek >= 20


def test_log_pesan_dan_jawaban(sesi):
    con = sesi['con']
    pid = con.execute("SELECT p.id FROM pesan p JOIN pengguna u ON u.id = p.pengguna_id WHERE p.sesi_id = ? "
                      "AND p.jenis = 'TANYA_HUJAN' AND u.pengguna_uji = 0", (sesi['sid'],)).fetchone()[0]
    uid = con.execute('SELECT pengguna_id FROM pesan WHERE id = ?', (pid,)).fetchone()[0]
    con.execute("INSERT INTO umpan_balik (pengguna_id, pesan_id, jenis, nilai, waktu_utc) VALUES "
                "(?, ?, 'JAWABAN_TADI_HUJAN', 'YA', ?)", (uid, pid, iso(TAU)))
    con.commit()
    d = sesi['penyaji'].keadaan()
    pesan = {(m['jam'], m['jenis']): m for m in d['pesan']}
    b = pesan[('06.30', 'BERPOTENSI')]
    assert b['status'] == 'TERKIRIM' and b['notifikasi'] and not b['isi'].startswith('[REPLAY')
    assert pesan[('06.00', 'RINGKASAN_PAGI')]['notifikasi'] is False
    assert pesan[('08.00', 'TANYA_HUJAN')]['jawaban'] == 'YA'
    assert all(m['n_hp'] == 1 for m in d['pesan'])                   # pesan pengguna uji tidak ikut
    # rekam jejak dashboard = kalimat yang dikirim ke HP pada saat itu (tau 06.30 untuk pesan BERPOTENSI)
    sesi['kendali'].atur(tau=dari_wib('2026-10-25 06:30'))
    try:
        rj = sesi['penyaji'].keadaan()['rekam_jejak']
    finally:
        sesi['kendali'].atur(tau=TAU)
    if rj['n'] >= 5:
        assert f"{rj['x']} dari {rj['n']} peringatan" in b['isi']


def test_ganti_stasiun_grafik(sesi):
    d = sesi['penyaji'].keadaan('bako')
    assert d['grafik']['kode'] == 'BAKO' and d['grafik']['tanda'] == []   # tanda pesan hanya untuk stasiun HP
    assert sesi['penyaji'].keadaan('XXXX')['grafik']['kode'] == 'CKRG'


def test_sebelum_sesi_hanya_kerangka(sesi):
    k = Kendali('CKRG', MULAI, SELESAI)
    d = Penyaji(sesi['path'], k, sesi['aturan']).keadaan()
    assert d['kendali']['fase'] == 'MENUNGGU_HP' and d['grafik'] is None and d['pesan'] == []
    assert len(d['stasiun']) == 4


def test_kendali():
    k = Kendali('CKRG', MULAI, SELESAI, 2.0)
    k.perintah('mulai'); assert not k.minta_mulai.is_set()          # belum SIAP
    k.atur(fase='SIAP'); k.perintah('mulai'); assert k.minta_mulai.is_set()
    k.perintah('jeda'); assert not k.jeda                             # jeda hanya saat berjalan
    k.atur(fase='BERJALAN'); k.perintah('jeda'); assert k.jeda
    k.perintah('lanjut'); assert not k.jeda
    k.perintah('kecepatan', 0.01); assert k.detik_per_tick == 0.2
    k.perintah('kecepatan', 'abc'); assert k.detik_per_tick == 0.2
    k.perintah('kecepatan', 3); assert k.detik_per_tick == 3.0


def _ambil(url, data=None):
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'} if data else {})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def test_http(sesi):
    k = Kendali('CKRG', MULAI, SELESAI, 2.0)
    k.atur(fase='BERJALAN', sesi_id=sesi['sid'], tau=TAU)
    srv, url = jalankan_server(sesi['path'], k, sesi['aturan'], port=0)
    try:
        assert url.startswith('http://127.0.0.1:')
        kode, isi = _ambil(url)
        assert kode == 200 and b'AngkatDulu' in isi and b'https://' not in isi   # tanpa CDN/internet
        kode, isi = _ambil(url + 'api/keadaan?kode=CJUR')
        assert kode == 200 and json.loads(isi)['grafik']['kode'] == 'CJUR'
        kode, isi = _ambil(url + 'api/kendali', json.dumps({'aksi': 'jeda'}).encode())
        assert kode == 200 and json.loads(isi)['jeda'] is True and k.jeda
        assert _ambil(url + 'api/kendali', b'{bukan json')[0] == 400
        assert _ambil(url + 'tidak-ada')[0] == 404
    finally:
        srv.shutdown(); srv.server_close()
