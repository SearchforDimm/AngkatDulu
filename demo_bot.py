"""Jalankan demo AngkatDulu: mesin replay + bot Telegram + dashboard lokal (untuk Demo Day dan video).

Token bot dibaca dari config/.env (TELEGRAM_BOT_TOKEN). Bot butuh internet (tanpa IP publik); dashboard tidak.

Contoh:
  python demo_bot.py --replay                # bot + dashboard; tunggu HP mendaftar, lalu tekan "Mulai replay"
  python demo_bot.py --replay --tanpa-bot    # tanpa internet: dashboard saja, pesan hanya tampil di panel
  python demo_bot.py                         # layani pendaftaran HP saja (Ctrl+C untuk berhenti)
  python demo_bot.py --replay --detik-per-tick 3 --mulai "2026-10-25 05:00" --selesai "2026-10-25 20:00"

Dashboard terbuka otomatis di http://127.0.0.1:8000/. Replay menunggu tombol "Mulai replay" di dashboard,
lalu bisa dijeda, diubah kecepatannya, dan diputar ulang dari sana.

Mode demo (default): lokasi yang dikirim HP diganti titik jemur contoh dekat stasiun --stasiun (CKRG),
supaya demo di mana pun tetap memakai data Karawang. Pakai --lokasi-asli untuk memakai lokasi sebenarnya.
"""
import argparse
import sys
import time
import webbrowser
from pathlib import Path

AKAR = Path(__file__).resolve().parent
sys.path.insert(0, str(AKAR))
from bot.layanan import PERINTAH, PenanganBot, PengirimTelegram  # noqa: E402
from bot.telegram import GalatTelegram, Telegram, baca_token  # noqa: E402
from dasbor.server import Kendali, jalankan_server  # noqa: E402
from mesin.mesin import PengirimLog  # noqa: E402
from mesin.periksa import periksa_pelanggaran  # noqa: E402
from mesin.waktu import SLOT, dari_wib, iso, label_wib  # noqa: E402
from replay import jalankan, siapkan_db  # noqa: E402


def pelanggan_nyata(con, kode):
    return con.execute('SELECT COUNT(*) FROM v_pelanggan_stasiun v JOIN pengguna p ON p.id = v.pengguna_id '
                       'WHERE v.kode_stasiun = ? AND p.pengguna_uji = 0', (kode,)).fetchone()[0]


def layani_selama(penangan, detik):
    """Layani update Telegram selama `detik` (long polling pendek supaya tepat waktu). Tanpa bot: tidur saja."""
    batas = time.monotonic() + detik
    while (sisa := batas - time.monotonic()) > 0:
        if penangan is None:
            time.sleep(min(sisa, 0.25)); continue
        try:
            penangan.layani(tunggu=max(0, min(int(sisa), 5)))
        except GalatTelegram as e:
            if 'Timeout' not in str(e):          # batas waktu long polling sesekali wajar; jangan ramaikan layar
                print(f'  ! {e}', flush=True)
            time.sleep(min(2, max(0.0, sisa)))


def ringkasan(con, sesi, aturan, nyata):
    print(f'\nSesi {sesi} selesai.', flush=True)
    for jenis, status, n in con.execute('SELECT jenis, status, COUNT(*) FROM pesan p JOIN pengguna u ON u.id = '
                                        'p.pengguna_id WHERE sesi_id = ? AND u.pengguna_uji = ? GROUP BY 1, 2 '
                                        'ORDER BY 1, 2', (sesi, 0 if nyata else 1)):
        print(f'  {jenis:15s} {status:11s} {n}')
    print('Pelanggaran kebijakan pesan:', len(periksa_pelanggaran(con, sesi, aturan)), flush=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--db', default=str(AKAR / 'angkatdulu.db'))
    ap.add_argument('--aturan', default=str(AKAR / 'config' / 'aturan.yaml'))
    ap.add_argument('--env', default=str(AKAR / 'config' / '.env'))
    ap.add_argument('--stasiun', default='CKRG')
    ap.add_argument('--lokasi-asli', action='store_true', help='pakai lokasi HP sebenarnya (bukan titik contoh)')
    ap.add_argument('--replay', action='store_true', help='putar replay (dengan bot: setelah ada HP terdaftar)')
    ap.add_argument('--mulai', default='2026-10-25 05:00', help='WIB')
    ap.add_argument('--selesai', default='2026-10-25 20:00', help='WIB')
    ap.add_argument('--detik-per-tick', type=float, default=2.0, help='detik nyata per 30 menit simulasi (awal)')
    ap.add_argument('--pemanasan-hari', type=float, default=30)
    ap.add_argument('--tanpa-bot', action='store_true', help='tanpa Telegram/internet: pesan hanya di dashboard')
    ap.add_argument('--tanpa-dasbor', action='store_true', help='tanpa dashboard: replay langsung jalan')
    ap.add_argument('--tanpa-browser', action='store_true', help='jangan buka browser otomatis')
    ap.add_argument('--port', type=int, default=8000, help='port dashboard (127.0.0.1)')
    ap.add_argument('--langsung', action='store_true', help='putaran pertama mulai tanpa menunggu tombol Mulai')
    ap.add_argument('--layani-setelah', type=float, default=120,
                    help='tanpa dashboard: detik melayani jawaban setelah replay selesai')
    ap.add_argument('--api', default='https://api.telegram.org', help=argparse.SUPPRESS)   # uji dengan server tiruan
    x = ap.parse_args(argv)
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
    kode = x.stasiun.upper()

    tg = None; nama_bot = None
    if not x.tanpa_bot:
        try:
            tg = Telegram(baca_token(x.env), alamat=x.api)
            nama_bot = tg.saya()['username']
            tg.hapus_webhook()
            tg.atur_perintah(PERINTAH)
        except GalatTelegram as e:
            sys.exit(f'Bot tidak bisa tersambung: {e}\nTanpa internet? Jalankan dengan --tanpa-bot.')
        print(f'Bot @{nama_bot} tersambung. Buka https://t.me/{nama_bot} di HP, tekan Start, lalu kirim lokasi.',
              flush=True)
    elif not x.replay:
        sys.exit('--tanpa-bot hanya berguna bersama --replay.')

    con, aturan, aid = siapkan_db(x.db, x.aturan)
    penangan = PenanganBot(con, tg, stasiun_demo=None if x.lokasi_asli else kode) if tg else None

    if not x.replay:
        print('Melayani pendaftaran. Ctrl+C untuk berhenti.', flush=True)
        try:
            while True:
                layani_selama(penangan, 60)
        except KeyboardInterrupt:
            return

    mulai, selesai = dari_wib(x.mulai), dari_wib(x.selesai)
    kendali = Kendali(kode, mulai, selesai, x.detik_per_tick, bot=nama_bot)
    kendali.pemanasan_hari = x.pemanasan_hari
    if not x.tanpa_dasbor:
        try:
            _, url = jalankan_server(x.db, kendali, aturan, x.port)
        except OSError:
            _, url = jalankan_server(x.db, kendali, aturan, 0)        # port terpakai: pilih port bebas
        print(f'Dashboard: {url}', flush=True)
        if not x.tanpa_browser:
            webbrowser.open(url)

    try:
        if penangan is not None:
            print(f'Menunggu minimal 1 HP terdaftar di stasiun {kode} ...', flush=True)
            while pelanggan_nyata(con, kode) == 0:
                layani_selama(penangan, 2)
        putar(con, aturan, aid, x, kode, kendali, tg, penangan, mulai, selesai)
    except KeyboardInterrupt:
        print('\nBerhenti.', flush=True)


def putar(con, aturan, aid, x, kode, kendali, tg, penangan, mulai, selesai):
    """Satu atau beberapa putaran replay. Dengan dashboard: tunggu Mulai; Putar ulang membuat sesi baru."""
    pakai_tombol = not x.tanpa_dasbor
    putaran = 0
    while True:
        putaran += 1
        kendali.minta_mulai.clear()
        n_hp = pelanggan_nyata(con, kode)
        kendali.atur(fase='PEMANASAN', sesi_id=None, tau=None, jeda=False, n_hp=n_hp)
        print(f'{n_hp} HP terdaftar. Memanaskan mesin {x.pemanasan_hari:.0f} hari (±1 menit) ...', flush=True)
        sekarang = {'tau': mulai}
        if penangan is not None:
            penangan.waktu = lambda: sekarang['tau']
            penangan.mesin = None

        def sebelum_mulai(m):
            if penangan is not None:
                penangan.mesin = m
            kendali.atur(fase='SIAP', sesi_id=m.sesi_id, tau=mulai - SLOT)
            if pakai_tombol and not (x.langsung and putaran == 1):
                print('Siap. Tekan "Mulai replay" di dashboard.', flush=True)
                while not kendali.minta_mulai.is_set():
                    layani_selama(penangan, 0.5)
                    kendali.atur(n_hp=pelanggan_nyata(con, kode))
            kendali.minta_mulai.clear()
            kendali.atur(fase='BERJALAN')
            print(f'Replay mulai: {label_wib(mulai)} sampai {label_wib(selesai)}.', flush=True)

        def setelah_tick(m, tau):
            sekarang['tau'] = tau
            kendali.atur(tau=tau)
            r = con.execute('SELECT pwv_1jam_mm, persentil FROM status_stasiun WHERE sesi_id = ? AND kode_stasiun = ? '
                            'AND waktu_utc = ?', (m.sesi_id, kode, iso(tau))).fetchone() or (None, None)
            pwv = f'PWV {r[0]:5.1f} mm, persentil {r[1]:3.0f}' if r[0] is not None and r[1] is not None else 'PWV -'
            print(f'{label_wib(tau)}  {kode} {m.penilai[kode].level:11s} {pwv}', flush=True)
            layani_selama(penangan, kendali.detik_per_tick)
            while kendali.jeda:
                layani_selama(penangan, 0.3)

        pengirim = PengirimTelegram(con, tg) if tg else PengirimLog(cetak=True)
        m, sesi = jalankan(con, aturan, aid, mulai, selesai, stasiun=[kode], pemanasan_hari=x.pemanasan_hari,
                           nama=f'demo {label_wib(mulai)}', pengirim=pengirim,
                           sebelum_mulai=sebelum_mulai, setelah_tick=setelah_tick)
        kendali.atur(fase='SELESAI')
        ringkasan(con, sesi, aturan, nyata=tg is not None)

        if not pakai_tombol:
            if x.layani_setelah > 0 and penangan is not None:
                print(f'Masih melayani jawaban selama {x.layani_setelah:.0f} detik ...', flush=True)
                layani_selama(penangan, x.layani_setelah)
            return
        print('Tekan "Putar ulang" di dashboard untuk sesi baru, atau Ctrl+C untuk keluar.', flush=True)
        while not kendali.minta_mulai.is_set():
            layani_selama(penangan, 0.5)


if __name__ == '__main__':
    main()
