"""Kebijakan pesan (PRD 8.4) dan histeresis status, diuji tanpa database."""
from mesin.aturan import Aturan, PenilaiAturan
from mesin.kebijakan import KuotaMemori, putuskan, transisi
from mesin.waktu import dari_wib


def aturan():
    return Aturan(nama='uji', versi='0', jenis='persentil', l2_min=80, l1_min=65)


def test_jam_notifikasi():
    a = aturan()
    assert putuskan('BERPOTENSI', dari_wib('2026-10-27 05:30'), 0, False, a) == ('DITAHAN', 'DI_LUAR_JAM')
    assert putuskan('BERPOTENSI', dari_wib('2026-10-27 06:00'), 0, False, a) == ('DIJADWALKAN', None)
    assert putuskan('BERPOTENSI', dari_wib('2026-10-27 17:30'), 0, False, a) == ('DIJADWALKAN', None)
    assert putuskan('BERPOTENSI', dari_wib('2026-10-27 18:00'), 0, False, a) == ('DITAHAN', 'DI_LUAR_JAM')


def test_kuota_mencakup_aman_lagi():
    a = aturan(); k = KuotaMemori()
    assert k.putuskan('BERPOTENSI', dari_wib('2026-10-27 09:00'), a)[0] == 'DIJADWALKAN'
    assert k.putuskan('AMAN_LAGI', dari_wib('2026-10-27 11:00'), a)[0] == 'DIJADWALKAN'
    assert k.putuskan('BERPOTENSI', dari_wib('2026-10-27 13:00'), a) == ('DITAHAN', 'KUOTA_HARIAN')
    assert k.putuskan('BERPOTENSI', dari_wib('2026-10-28 09:00'), a)[0] == 'DIJADWALKAN'   # hari baru


def test_aman_lagi_butuh_berpotensi_hari_itu():
    a = aturan(); k = KuotaMemori()
    assert k.putuskan('AMAN_LAGI', dari_wib('2026-10-27 10:00'), a) is None
    k.putuskan('BERPOTENSI', dari_wib('2026-10-26 16:00'), a)
    assert k.putuskan('AMAN_LAGI', dari_wib('2026-10-27 08:00'), a) is None                # BERPOTENSI kemarin


def test_aman_lagi_hanya_selama_masih_bisa_menjemur():
    """'Aman lagi' berarti 'boleh jemur lagi', jadi tidak dikirim setelah 15.00 WIB (review proposal poin 6)."""
    a = aturan(); k = KuotaMemori()
    assert a.aman_lagi_sampai == 15.0
    k.putuskan('BERPOTENSI', dari_wib('2026-10-25 06:30'), a)
    assert k.putuskan('AMAN_LAGI', dari_wib('2026-10-25 16:30'), a) == ('DITAHAN', 'LEWAT_JAM_JEMUR')
    assert k.putuskan('AMAN_LAGI', dari_wib('2026-10-25 14:30'), a) == ('DIJADWALKAN', None)
    k2 = KuotaMemori(); k2.putuskan('BERPOTENSI', dari_wib('2026-10-25 06:30'), a)
    k2.putuskan('AMAN_LAGI', dari_wib('2026-10-25 16:30'), a)                         # ditahan: kuota tidak terpakai
    assert k2.putuskan('BERPOTENSI', dari_wib('2026-10-25 17:00'), a) == ('DIJADWALKAN', None)


def test_transisi():
    assert transisi('AMAN', 'BERPOTENSI') == 'BERPOTENSI'
    assert transisi('WASPADA', 'BERPOTENSI') == 'BERPOTENSI'
    assert transisi('TANPA_DATA', 'BERPOTENSI') == 'BERPOTENSI'
    assert transisi('BERPOTENSI', 'WASPADA') == 'AMAN_LAGI'
    assert transisi('BERPOTENSI', 'AMAN') == 'AMAN_LAGI'
    assert transisi('BERPOTENSI', 'TANPA_DATA') is None
    assert transisi('AMAN', 'WASPADA') is None                    # Level 1 tidak di-push


def f(p):
    return dict(pwv_1jam=40.0, anomali=0.0, persentil=p, delta_3j=0.0, ada=True)


def test_histeresis_dan_tanpa_data():
    pen = PenilaiAturan(aturan())
    assert pen.nilai(f(50)) == 'AMAN'
    assert pen.nilai(f(70)) == 'WASPADA'
    assert pen.nilai(f(85)) == 'BERPOTENSI'
    assert pen.nilai(f(70)) == 'BERPOTENSI'          # syarat Level 2 hilang 30 menit: tetap
    assert pen.nilai(f(70)) == 'WASPADA'             # 60 menit: BERPOTENSI padam, Level 1 masih terpenuhi
    assert pen.nilai(f(50)) == 'WASPADA'             # Level 1 hilang 30 menit: tetap
    assert pen.nilai(f(50)) == 'AMAN'
    assert pen.nilai(f(85)) == 'BERPOTENSI'
    assert pen.nilai(f(50)) == 'BERPOTENSI'
    assert pen.nilai(f(50)) == 'AMAN'                # keduanya hilang 60 menit: langsung AMAN
    assert pen.nilai(f(90)) == 'BERPOTENSI'
    for _ in range(3):
        assert pen.nilai(None) == 'BERPOTENSI'       # data putus < 2 jam: status dipertahankan
    assert pen.nilai(None) == 'TANPA_DATA'           # 2 jam
    assert pen.nilai(f(50)) == 'AMAN'
