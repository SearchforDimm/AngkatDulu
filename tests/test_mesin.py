"""Mesin replay: perilaku sama dengan kalibrasi, 0 pelanggaran kebijakan, kinerja, dan ganti aturan (US-10)."""
import time

import numpy as np
import pandas as pd
import pytest
import yaml

import kalibrasi as K
from mesin.basisdata import muat_aturan
from mesin.periksa import periksa_pelanggaran
from mesin.waktu import dari_wib, ke_utc
from replay import jalankan

SETENGAH = pd.Timedelta(minutes=30)


@pytest.mark.parametrize('kode', ['CKRG', 'CJUR'])
def test_mesin_sama_dengan_kalibrasi(db, folder_data, kode):
    """Status BERPOTENSI tiap tick dan waktu notifikasi BERPOTENSI = hasil simulasi kalibrasi (1 Sep–1 Nov)."""
    con, aturan, aid = db
    awal = ke_utc(K.GRID_MULAI) + SETENGAH
    m, sesi = jalankan(con, aturan, aid, awal, ke_utc(K.GRID_AKHIR) + SETENGAH, [kode], pemanasan_hari=0)
    st = pd.read_sql_query('SELECT waktu_utc, level FROM status_stasiun WHERE sesi_id = ? AND kode_stasiun = ? '
                           'ORDER BY waktu_utc', con, params=(sesi, kode))
    f = K.fitur_stasiun(folder_data, kode, aturan.jendela_hari)
    on, kirim = K.simulasi(f, K.syarat_aturan(f, aturan), f.ada.to_numpy(), aturan)
    assert len(st) == len(f)
    assert np.array_equal((st.level == 'BERPOTENSI').to_numpy(), on)
    terkirim = pd.read_sql_query("SELECT dijadwalkan_utc FROM pesan WHERE sesi_id = ? AND jenis = 'BERPOTENSI' "
                                 "AND status = 'TERKIRIM' ORDER BY dijadwalkan_utc", con, params=(sesi,))
    harap = [t.strftime('%Y-%m-%dT%H:%M:%SZ') for t in f.index[kirim] + SETENGAH]
    assert list(terkirim.dijadwalkan_utc) == harap
    assert periksa_pelanggaran(con, sesi, aturan) == []


def test_replay_11_hari_cepat_dan_patuh(db):
    con, aturan, aid = db
    t0 = time.time()
    m, sesi = jalankan(con, aturan, aid, dari_wib('2026-10-21 00:00'), dari_wib('2026-10-31 23:30'), ['CKRG'],
                       pemanasan_hari=15)
    assert time.time() - t0 < 300                                      # NFR: 11 hari <= 5 menit
    assert periksa_pelanggaran(con, sesi, aturan) == []
    p = pd.read_sql_query('SELECT * FROM pesan WHERE sesi_id = ?', con, params=(sesi,))
    assert (p.jenis == 'RINGKASAN_PAGI').sum() == 11                   # satu per hari, 06.00 WIB
    assert p.isi.str.startswith('[REPLAY · ').all()
    assert (p.dijadwalkan_utc >= '2026-10-20T17:00:00Z').all()          # tidak ada pesan saat pemanasan
    b = p[(p.jenis == 'BERPOTENSI') & (p.status == 'TERKIRIM')]
    t = p[p.jenis == 'TANYA_HUJAN']
    assert len(t) == len(b) and set(t.peringatan_id) == set(b.peringatan_id)
    # pesan hanya untuk CKRG, tetapi 4 stasiun dipantau dan rekam jejak digabung
    st = {r[0] for r in con.execute('SELECT DISTINCT kode_stasiun FROM status_stasiun WHERE sesi_id = ?', (sesi,))}
    assert st == {'CKRG', 'BAKO', 'CLBG', 'CJUR'}
    assert len(b) > 0 and b.isi.str.contains('di 4 stasiun').all()
    assert set(p.pengguna_id) <= {r[0] for r in con.execute(
        "SELECT pengguna_id FROM v_pelanggan_stasiun WHERE kode_stasiun = 'CKRG'")}


def test_ganti_aturan_tanpa_ubah_kode(db, tmp_path):
    con, aturan, aid = db
    d = yaml.safe_load(open(K.AKAR / 'config' / 'aturan.yaml', encoding='utf-8'))
    d['versi'] = '9.9.9-uji'; d['level2']['min'] = 90
    path = tmp_path / 'aturan_uji.yaml'; path.write_text(yaml.safe_dump(d, allow_unicode=True), encoding='utf-8')
    a2, aid2 = muat_aturan(con, path)
    assert aid2 != aid and a2.l2_min == 90
    m, sesi = jalankan(con, a2, aid2, dari_wib('2026-10-27 05:00'), dari_wib('2026-10-27 08:00'), ['CKRG'],
                       pemanasan_hari=1)
    ids = {r[0] for r in con.execute('SELECT DISTINCT aturan_id FROM status_stasiun WHERE sesi_id = ?', (sesi,))}
    assert ids == {aid2}
