"""Template pesan (PRD 8.5). Bahasa sederhana, maksimal 3 kalimat, selalu menyebut stasiun dan jarak."""
from .waktu import label_wib

STATUS_TEKS = {
    'AMAN': 'aman: udara relatif kering',
    'WASPADA': 'waspada: udara lembap, jemur dekat terpal',
    'BERPOTENSI': 'berpotensi hujan dalam 3 jam',
    'TANPA_DATA': 'data stasiun sedang terputus',
}
SARAN_PAGI = {
    'AMAN': 'Silakan menjemur, kami kabari bila berubah.',
    'WASPADA': 'Boleh menjemur, tapi siapkan terpal di dekat Anda.',
    'BERPOTENSI': 'Sebaiknya tunda menjemur atau siapkan terpal.',
    'TANPA_DATA': 'Perhatikan langit sendiri dulu, ya.',
}


def label(tau, mode):
    return f'[REPLAY · {label_wib(tau)}] ' if mode == 'REPLAY' else ''


def sumber(kode, jarak_km):
    return f'(data stasiun {kode}, ±{jarak_km:.0f} km dari lokasi Anda)'


def sambutan():
    return ('Halo, ini AngkatDulu. Kirim lokasi tempat Anda menjemur sekali saja. '
            'Kami kabari kalau berpotensi hujan dan kapan aman menjemur lagi.')


def info_jarak(kode, nama, jarak_km):
    return f'Lokasi Anda ±{jarak_km:.0f} km dari stasiun {kode} ({nama}). Data stasiun ini yang kami pakai.'


def kondisi_awal(level):
    return f'Saat ini status {STATUS_TEKS[level]}. Kami bantu pantau.'


def ringkasan_pagi(tren, level, kode, jarak_km):
    buka = f'Selamat pagi, uap air 24 jam terakhir {tren}.' if tren else 'Selamat pagi.'
    return f'{buka} Status pagi ini {STATUS_TEKS[level]} {sumber(kode, jarak_km)}. {SARAN_PAGI[level]}'


def berpotensi(kode, jarak_km, rekam_jejak):
    return (f'Berpotensi hujan dalam 3 jam di sekitar stasiun {kode} (±{jarak_km:.0f} km dari Anda). '
            f'Siapkan terpal atau angkat jemuran. {rekam_jejak}')


def aman_lagi(level, kode, jarak_km):
    if level == 'WASPADA':
        return (f'Peluang hujan menurun {sumber(kode, jarak_km)}. '
                'Udara masih lembap, jadi boleh menjemur lagi dengan terpal di dekat Anda.')
    return f'Udara kembali lebih kering {sumber(kode, jarak_km)}. Anda bisa menjemur lagi.'


def tanya_hujan():
    return 'Tadi hujan di tempat Anda?'


def terima_laporan():
    return 'Terima kasih, laporan hujan Anda tercatat.'


def rekam_jejak(x, n, n_stasiun=1):
    """Rekam jejak gabungan semua stasiun yang dipantau (bukan hanya stasiun pengguna)."""
    tempat = f'di {n_stasiun} stasiun' if n_stasiun > 1 else 'di stasiun ini'
    if n < 5:
        return f'Rekam jejak {tempat} belum cukup.'
    return f'Bulan lalu {tempat}, {x} dari {n} peringatan siang serupa diikuti hujan.'
