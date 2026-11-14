"""Hitungan evaluasi: notifikasi per hari hanya dihitung pada hari yang dinilai (ada PWV siang)."""
import numpy as np

import kalibrasi as K


def test_tebakan_jam_rawan_paling_banyak_satu_notifikasi_per_hari(folder_data):
    a0 = K.aturan_uji('anomali', None, None, 15)
    for s in K.STASIUN:
        f = K.fitur_stasiun(folder_data, s, 15); aw = K.awal_layak(folder_data, s, f)
        st, kirim = K.simulasi(f, f.bl_pola_harian.to_numpy(), np.ones(len(f), bool), a0)
        r = K.nilai(f, st, kirim, aw)
        for b in (9, 10):
            assert r[b]['kirim'] <= r[b]['hari'], (s, b, r[b]['kirim'], r[b]['hari'])
            assert r[b]['kirim_palsu'] <= r[b]['kirim']
