"""Mesin tidak pernah melihat data masa depan, dan fitur per tick = fitur kalibrasi."""
import numpy as np
import pandas as pd
import pytest

import kalibrasi as K
from mesin.mesin import Mesin
from mesin.sumber import ReplaySource
from mesin.waktu import ke_utc

POTONG = ['2026-09-05 04:00', '2026-09-26 08:30', '2026-10-10 07:00', '2026-10-27 01:00', '2026-11-01 23:30']


def test_fitur_tidak_bergantung_awal_potongan(folder_data):
    """Fitur per tick dihitung dari potongan data; nilainya harus identik (sampai bit) dengan seri penuh,
    karena persentil membandingkan nilai yang sering seri (PWV dibulatkan 2 desimal)."""
    from mesin.fitur import hitung_fitur, seri_layak
    p = pd.read_csv(folder_data / 'pwv_30menit_bako.csv', parse_dates=['waktu_utc'])
    v = seri_layak(p, mulai=K.GRID_MULAI, akhir=K.GRID_AKHIR)
    penuh = hitung_fitur(v, 15, 3, awal_seri=K.GRID_MULAI)
    for awal in ('2026-09-29', '2026-10-05 13:30', '2026-10-15 00:30'):
        a0 = ke_utc(awal)
        bag = hitung_fitur(v[a0:a0 + pd.Timedelta(days=16, hours=5)], 15, 3, awal_seri=K.GRID_MULAI, hanya_akhir=True)
        # slot pertama potongan tidak punya slot sebelumnya (mesin mengambil cadangan 16 hari, jadi tidak terpakai)
        a, b = bag.pwv_1jam.to_numpy()[1:], penuh.pwv_1jam.reindex(bag.index).to_numpy()[1:]
        assert np.array_equal(a, b, equal_nan=True), awal
        x, y = bag.persentil.iloc[-1], penuh.persentil.loc[bag.index[-1]]
        assert x == y or (np.isnan(x) and np.isnan(y)), (awal, x, y)


def test_sumber_hanya_slot_selesai(db):
    con, _, _ = db
    s = ReplaySource(con)
    for kode in K.STASIUN:
        for t in POTONG:
            v = s.ambil(kode, ke_utc(t))
            assert v.index.max() + pd.Timedelta(minutes=30) <= ke_utc(t)


@pytest.mark.parametrize('kode', K.STASIUN)
def test_fitur_tick_sama_dengan_kalibrasi(db, folder_data, kode):
    con, aturan, aid = db
    m = Mesin(con, aturan, aid, ReplaySource(con))
    penuh = K.fitur_stasiun(folder_data, kode, aturan.jendela_hari)
    rng = np.random.default_rng(7)
    waktu = list(map(ke_utc, POTONG)) + list(penuh.index[rng.choice(len(penuh), 40, replace=False)] + pd.Timedelta(minutes=30))
    for tau in waktu:
        f = m.fitur_saat(kode, tau)
        g = penuh.loc[tau - pd.Timedelta(minutes=30)]
        for kol in ('pwv_1jam', 'anomali', 'persentil', 'delta_3j'):
            a, b = f[kol], g[kol]
            assert (np.isnan(a) and np.isnan(b)) or abs(a - b) < 1e-9, (kode, tau, kol, a, b)
        assert bool(f['ada']) == bool(g['ada'])
