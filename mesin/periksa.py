"""Pemeriksa kebijakan pesan pada log satu sesi (target: 0 pelanggaran, PRD 12)."""
import pandas as pd

from .kebijakan import NOTIFIKASI
from .waktu import WIB


def _kalimat(teks):
    isi = teks.split('] ', 1)[-1]
    return sum(isi.count(x) for x in ('. ', '? ', '! ')) + (1 if isi.rstrip()[-1:] in '.?!' else 0)


def periksa_pelanggaran(con, sesi_id, aturan):
    p = pd.read_sql_query('SELECT * FROM pesan WHERE sesi_id = ?', con, params=(sesi_id,))
    salah = []
    if p.empty:
        return salah
    p['waktu'] = pd.to_datetime(p.dijadwalkan_utc, utc=True)
    p['wib'] = p.waktu.dt.tz_localize(None) + WIB
    p['tanggal'] = p.wib.dt.date
    kirim = p[p.status == 'TERKIRIM']
    notif = kirim[kirim.jenis.isin(NOTIFIKASI)]
    jam = notif.wib.dt.hour + notif.wib.dt.minute / 60
    for _, r in notif[(jam < aturan.jam_mulai) | (jam >= aturan.jam_selesai)].iterrows():
        salah.append(f'notifikasi {r.jenis} {r.id} di luar jam')
    for (u, d), n in notif.groupby(['pengguna_id', 'tanggal']).size().items():
        if n > aturan.maks_per_hari:
            salah.append(f'pengguna {u} tanggal {d}: {n} notifikasi')
    for _, r in notif[notif.jenis == 'AMAN_LAGI'].iterrows():
        sebelum = notif[(notif.pengguna_id == r.pengguna_id) & (notif.tanggal == r.tanggal) &
                        (notif.jenis == 'BERPOTENSI') & (notif.waktu < r.waktu)]
        if sebelum.empty:
            salah.append(f'AMAN_LAGI {r.id} tanpa BERPOTENSI sebelumnya')
        if r.wib.hour + r.wib.minute / 60 >= aturan.aman_lagi_sampai:
            salah.append(f'AMAN_LAGI {r.id} setelah jam jemur')
    tidak_boleh = kirim[~kirim.jenis.isin(NOTIFIKASI) & (kirim.sebagai_notifikasi == 1)]
    for _, r in tidak_boleh.iterrows():
        salah.append(f'{r.jenis} {r.id} dikirim berbunyi')
    for _, r in kirim[kirim.jenis == 'TANYA_HUJAN'].iterrows():
        b = p[(p.pengguna_id == r.pengguna_id) & (p.jenis == 'BERPOTENSI') & (p.peringatan_id == r.peringatan_id)]
        if b.empty or (r.waktu - b.waktu.iloc[0]) != pd.Timedelta(minutes=aturan.tanya_hujan_menit):
            salah.append(f'TANYA_HUJAN {r.id} tidak {aturan.tanya_hujan_menit} menit setelah BERPOTENSI')
    for _, r in p.iterrows():
        if _kalimat(r.isi) > 3:
            salah.append(f'pesan {r.id} lebih dari 3 kalimat')
        if r.jenis in ('BERPOTENSI', 'AMAN_LAGI', 'RINGKASAN_PAGI') and 'stasiun' not in r.isi:
            salah.append(f'pesan {r.id} tidak menyebut stasiun')
    return salah
