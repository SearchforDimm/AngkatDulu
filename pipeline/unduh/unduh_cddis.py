"""Unduh orbit (SP3) dan jam (CLK) CODE dari CDDIS untuk banyak DOY sekaligus.

Pemakaian (di laptop, butuh Python 3 dan paket requests: pip install requests):
    python unduh_cddis.py --doy 244-290,304-306
    python unduh_cddis.py --doy 244-290 --cek        # hanya menampilkan URL, tidak mengunduh

Login memakai akun Earthdata (sama dengan Giovanni). Script menanyakan username dan password,
atau membaca file .netrc / _netrc di folder home bila ada:
    machine urs.earthdata.nasa.gov login USERNAME password PASSWORD

Urutan pencarian per hari:
    1) final MGEX : archive/gnss/products/<minggu GPS>/COD0MGXFIN_...  (lalu folder lama mgex/<minggu>/)
    2) final CODE : archive/gnss/products/<minggu GPS>/COD0OPSFIN_...
    3) rapid CODE : archive/gnss/products/<minggu GPS>/COD0OPSRAP_...
File .gz disimpan apa adanya di folder --out; kirim folder itu (di-zip) ke Claude.
"""
import argparse, datetime as dt, getpass, netrc, os, sys, time
import requests

BASE = 'https://cddis.nasa.gov/archive/gnss/products'
AUTH_HOST = 'urs.earthdata.nasa.gov'


class SesiEarthdata(requests.Session):
    """Pola resmi NASA: header Authorization hanya dikirim ke host Earthdata."""
    def rebuild_auth(self, prepared_request, response):
        headers = prepared_request.headers
        if 'Authorization' in headers:
            asal = requests.utils.urlparse(response.request.url).hostname
            tujuan = requests.utils.urlparse(prepared_request.url).hostname
            if asal != tujuan and tujuan != AUTH_HOST and asal != AUTH_HOST:
                del headers['Authorization']


def kredensial():
    for nama in ('.netrc', '_netrc'):
        p = os.path.join(os.path.expanduser('~'), nama)
        if os.path.exists(p):
            try:
                a = netrc.netrc(p).authenticators(AUTH_HOST)
                if a:
                    return a[0], a[2]
            except Exception:
                pass
    u = input('Username Earthdata: ').strip()
    return u, getpass.getpass('Password Earthdata: ')


def daftar_doy(teks):
    hasil = []
    for bagian in teks.split(','):
        if '-' in bagian:
            a, b = bagian.split('-')
            hasil += list(range(int(a), int(b) + 1))
        else:
            hasil.append(int(bagian))
    return sorted(set(hasil))


def minggu_gps(tahun, doy):
    tgl = dt.date(tahun, 1, 1) + dt.timedelta(days=doy - 1)
    return (tgl - dt.date(1980, 1, 6)).days // 7


def kandidat(tahun, doy):
    w = minggu_gps(tahun, doy)
    tag = f'{tahun}{doy:03d}0000_01D'
    def pasangan(folder, prefiks):
        return [f'{folder}/{prefiks}_{tag}_05M_ORB.SP3.gz', f'{folder}/{prefiks}_{tag}_30S_CLK.CLK.gz']
    return [
        ('MGEX_FINAL', pasangan(f'{BASE}/{w}', 'COD0MGXFIN')),        # lokasi sekarang (folder minggu)
        ('MGEX_FINAL', pasangan(f'{BASE}/mgex/{w}', 'COD0MGXFIN')),   # lokasi lama
        ('OPS_FINAL', pasangan(f'{BASE}/{w}', 'COD0OPSFIN')),         # CODE final GPS+GLONASS
        ('RAPID', pasangan(f'{BASE}/{w}', 'COD0OPSRAP')),
    ]


def unduh(sesi, url, tujuan, coba=3):
    for i in range(coba):
        try:
            r = sesi.get(url, timeout=120, stream=True)
            if r.status_code == 404:
                return 'TIDAK_ADA'
            r.raise_for_status()
            if 'text/html' in r.headers.get('Content-Type', ''):
                return 'LOGIN_GAGAL'   # biasanya berarti login Earthdata ditolak
            tmp = tujuan + '.part'
            with open(tmp, 'wb') as f:
                for blok in r.iter_content(1 << 16):
                    f.write(blok)
            os.replace(tmp, tujuan)
            return 'OK'
        except requests.RequestException as e:
            if i == coba - 1:
                return f'GAGAL ({e.__class__.__name__})'
            time.sleep(3 * (i + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--doy', required=True, help='mis. 244-290,304-306')
    ap.add_argument('--tahun', type=int, default=2026)
    ap.add_argument('--out', default='cddis_produk')
    ap.add_argument('--cek', action='store_true', help='tampilkan URL saja')
    ap.add_argument('--rinci', action='store_true', help='tampilkan hasil tiap URL')
    a = ap.parse_args()
    doys = daftar_doy(a.doy)
    if a.cek:
        for d in doys:
            print(d, 'minggu', minggu_gps(a.tahun, d))
            for jenis, urls in kandidat(a.tahun, d):
                for u in urls:
                    print('   ', jenis, u)
        return
    os.makedirs(a.out, exist_ok=True)
    sesi = SesiEarthdata()
    sesi.auth = kredensial()
    ringkas = []
    for d in doys:
        status = 'TIDAK_ADA'
        for jenis, urls in kandidat(a.tahun, d):
            hasil = []
            for u in urls:
                tujuan = os.path.join(a.out, u.rsplit('/', 1)[1])
                h = 'OK' if os.path.exists(tujuan) else unduh(sesi, u, tujuan)
                hasil.append(h)
                if a.rinci:
                    print('   ', h, u)
            if all(h == 'OK' for h in hasil):
                status = jenis
                break
            if any(h == 'LOGIN_GAGAL' for h in hasil):
                print('Login Earthdata ditolak. Cek username/password, lalu jalankan ulang.')
                sys.exit(1)
        print(f'DOY {d}: {status}')
        ringkas.append(f'{d},{minggu_gps(a.tahun, d)},{status}')
    with open(os.path.join(a.out, 'ringkasan_unduhan.csv'), 'w') as f:
        f.write('doy,minggu_gps,produk\n' + '\n'.join(ringkas) + '\n')
    kurang = [r for r in ringkas if r.endswith('TIDAK_ADA') or 'GAGAL' in r]
    print(f'Selesai. {len(doys) - len(kurang)} dari {len(doys)} hari lengkap. Folder: {a.out}')
    if kurang:
        print('Belum dapat:', ', '.join(r.split(',')[0] for r in kurang))


if __name__ == '__main__':
    main()
