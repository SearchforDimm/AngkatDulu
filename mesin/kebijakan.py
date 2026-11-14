"""Kebijakan pesan (PRD 8.4). Fungsi murni: dipakai PerencanaPesan di mesin dan simulasi di kalibrasi.

1. Notifikasi hanya untuk BERPOTENSI dan AMAN_LAGI, pukul jam_mulai–jam_selesai WIB.
2. Maksimal `maks_per_hari` notifikasi (BERPOTENSI + AMAN_LAGI) per chat per tanggal WIB.
3. AMAN_LAGI hanya bila hari itu sudah ada BERPOTENSI yang dikirim ke chat tersebut, dan hanya sampai
   `aman_lagi_sampai` (15.00 WIB): sesudah itu "boleh jemur lagi" tidak berguna dan menyesatkan.
4. TANYA_HUJAN, RINGKASAN_PAGI, dan jawaban perintah tidak menghitung kuota dan dikirim tanpa bunyi.
Pesan yang tidak boleh dikirim dicatat DITAHAN dengan alasan DI_LUAR_JAM, LEWAT_JAM_JEMUR, atau KUOTA_HARIAN.
"""
from .waktu import tanggal_wib, wib

NOTIFIKASI = ('BERPOTENSI', 'AMAN_LAGI')


def dalam_jam(tau, aturan):
    w = wib(tau); jam = w.hour + w.minute / 60
    return aturan.jam_mulai <= jam < aturan.jam_selesai


def putuskan(jenis, tau, n_notif_hari_ini, ada_berpotensi_hari_ini, aturan):
    """Kembali (status, alasan), atau None bila pesan tidak perlu dibuat sama sekali."""
    if jenis == 'AMAN_LAGI' and not ada_berpotensi_hari_ini:
        return None
    if not dalam_jam(tau, aturan):
        return 'DITAHAN', 'DI_LUAR_JAM'
    if jenis == 'AMAN_LAGI':
        w = wib(tau)
        if w.hour + w.minute / 60 >= aturan.aman_lagi_sampai:
            return 'DITAHAN', 'LEWAT_JAM_JEMUR'
    if n_notif_hari_ini >= aturan.maks_per_hari:
        return 'DITAHAN', 'KUOTA_HARIAN'
    return 'DIJADWALKAN', None


class KuotaMemori:
    """Penghitung kuota satu chat di memori (untuk simulasi kalibrasi)."""
    def __init__(self):
        self.n = {}; self.berpotensi = set()

    def putuskan(self, jenis, tau, aturan):
        hari = tanggal_wib(tau)
        hasil = putuskan(jenis, tau, self.n.get(hari, 0), hari in self.berpotensi, aturan)
        if hasil and hasil[0] == 'DIJADWALKAN':
            self.n[hari] = self.n.get(hari, 0) + 1
            if jenis == 'BERPOTENSI': self.berpotensi.add(hari)
        return hasil


def transisi(sebelum, sesudah):
    """Jenis pesan notifikasi yang dipicu perubahan level, atau None."""
    if sesudah == 'BERPOTENSI' and sebelum != 'BERPOTENSI':
        return 'BERPOTENSI'
    if sebelum == 'BERPOTENSI' and sesudah in ('AMAN', 'WASPADA'):
        return 'AMAN_LAGI'
    return None
