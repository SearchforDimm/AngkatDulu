"""ZTD 30 detik -> PWV 30 menit per stasiun, dengan tekanan dan suhu ERA5 (data kontrak pwv_30menit.csv).

python3 pwv.py ERA5_a.grib [ERA5_b.grib ...] ztd_<st>.csv KODE  -> pwv_30menit_<kode>.csv + pwv_30detik_<kode>.csv
Beberapa file GRIB boleh dipakai sekaligus (grid harus sama); jam yang sama diambil dari file terakhir.

Tekanan di stasiun:
  1. Tinggi tiap titik grid ERA5 ditaksir dari rata-rata tekanan permukaannya terhadap baris laut
     (lintang -6,0; semua titik laut Jawa), dengan rumus hipsometrik.
  2. Tiap jam, tekanan tiap titik grid diturunkan ke muka laut, diinterpolasi bilinear ke stasiun,
     lalu dinaikkan lagi ke tinggi ortometrik stasiun. Suhu 2 m diperlakukan sama dengan laju
     penurunan 6,5 K/km.
  3. Jam yang tidak ada di ERA5 ditandai ERA5_ISI / METEO_ISI dan diisi pola rata-rata per jam
     14 hari sebelum celah. Celah di tengah (ada ERA5 sesudahnya) juga ditambah anomali yang
     ditarik lurus dari 6 jam terakhir sebelum celah ke 6 jam pertama sesudahnya.
ZHD Saastamoinen, Tm Bevis (70,2 + 0,72 Ts), Pi dengan k2' = 22,1 K/hPa, k3 = 3,739e5 K^2/hPa.
"""
import math, sys
from pathlib import Path
import numpy as np, pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grib1

G, RD, LAPSE = 9.80665, 287.05, 0.0065
STASIUN = {   # lat, lon, tinggi ortometrik (m, EGM96), tinggi elipsoid (m)
    'CKRG': (-6.11118, 107.32803, 8.0, 27.6),
    'BAKO': (-6.49110, 106.84890, 140.1, 158.19),
    'CLBG': (-6.82444, 107.61560, 1308.9, 1329.83),   # PPP-static median DOY 291-297, N EGM96 20,9 m
    'CJUR': (-6.82209, 107.13815, 459.8, 479.9),      # PPP-static median DOY 246-252 & 291-297, N EGM96 20,1 m
}


def baca_era5(paths):
    if isinstance(paths, (str, Path)):
        paths = [paths]
    lats = lons = None
    sp, t2 = {}, {}
    for path in paths:
        m = grib1.read(path)
        if lats is None:
            lats, lons = m[0]['lats'], m[0]['lons']
        elif not (np.array_equal(lats, m[0]['lats']) and np.array_equal(lons, m[0]['lons'])):
            raise ValueError(f'{path}: grid ERA5 berbeda dari file pertama')
        for x in m:
            (sp if x['param'] == 134 else t2)[pd.Timestamp(x['time'])] = x['vals']
    waktu = sorted(set(sp) & set(t2))
    return lats, lons, waktu, np.array([sp[w] for w in waktu]) / 100.0, np.array([t2[w] for w in waktu])


def tinggi_grid(sp, t2):
    """Taksiran tinggi tiap titik grid (m) dari tekanan rata-rata terhadap baris laut lintang -6,0."""
    p0 = sp[:, 0, :].mean()
    pm, tm = sp.mean(0), t2.mean(0)
    h = np.zeros_like(pm)
    for _ in range(3):   # suhu rata-rata lapisan bergantung pada h
        tv = tm + LAPSE * h / 2 + 3.0          # +3 K koreksi suhu virtual (udara lembap tropis)
        h = RD * tv / G * np.log(p0 / pm)
    return h


def bilinear(lats, lons, f, lat, lon):
    i = np.searchsorted(-lats, -lat) - 1; j = np.searchsorted(lons, lon) - 1
    wy = (lat - lats[i]) / (lats[i + 1] - lats[i]); wx = (lon - lons[j]) / (lons[j + 1] - lons[j])
    return (f[..., i, j] * (1 - wx) * (1 - wy) + f[..., i, j + 1] * wx * (1 - wy)
            + f[..., i + 1, j] * (1 - wx) * wy + f[..., i + 1, j + 1] * wx * wy)


def meteo_stasiun(path, kode, mulai, selesai):
    lat, lon, h_st, _ = STASIUN[kode]
    lats, lons, waktu, sp, t2 = baca_era5(path)
    h = tinggi_grid(sp, t2)
    tv_g = t2 + LAPSE * h / 2 + 3.0
    p_msl = sp * np.exp(G * h / (RD * tv_g))                 # ke muka laut
    t_msl = t2 + LAPSE * h
    pm, tmsl = bilinear(lats, lons, p_msl, lat, lon), bilinear(lats, lons, t_msl, lat, lon)
    t_st = tmsl - LAPSE * h_st
    p_st = pm * np.exp(-G * h_st / (RD * (t_st + LAPSE * h_st / 2 + 3.0)))
    era = pd.DataFrame({'tekanan_hpa': p_st, 'suhu_k': t_st}, index=pd.DatetimeIndex(waktu))
    idx = pd.date_range(mulai.floor('1h'), selesai.ceil('1h'), freq='1h')
    akhir = era.index.max()
    era, celah = isi_celah(era.reindex(era.index.union(idx)))
    era = era.reindex(idx)
    info = dict(era5_terakhir=akhir, celah=[c for c in celah if c[1] >= idx[0] and c[0] <= idx[-1]],
                tinggi_grid=pd.DataFrame(h, index=lats, columns=lons).round(0))
    return era, info


def isi_celah(era, kolom=('tekanan_hpa', 'suhu_k'), hari_pola=14, jam_tepi=6):
    """Isi jam kosong (deret per jam). Kembali (era + sumber_meteo, daftar celah (awal, akhir, n_jam, jenis)).

    Pola = rata-rata per jam 14 hari sebelum celah. Celah tengah: pola + anomali (asli - pola) yang
    ditarik lurus dari rata-rata 6 jam sebelum ke 6 jam sesudah celah. Celah ujung: pola saja.
    """
    era = era.asfreq('1h')
    kosong = era[kolom[0]].isna()
    era['sumber_meteo'] = np.where(kosong, 'ERA5_ISI', 'ERA5')
    grup = (kosong != kosong.shift()).cumsum()[kosong]
    celah = []
    for _, jam in grup.groupby(grup):
        a, b = jam.index[0], jam.index[-1]
        sebelum = era.loc[a - pd.Timedelta(days=hari_pola):a - pd.Timedelta(hours=1)].dropna(subset=list(kolom))
        sesudah = era.loc[b + pd.Timedelta(hours=1):].dropna(subset=list(kolom)).iloc[:jam_tepi]
        if sebelum.empty:
            continue
        pola = sebelum.groupby(sebelum.index.hour)[list(kolom)].mean()
        tengah = len(sesudah) > 0
        for c in kolom:
            isi = pd.Series(pola[c].reindex(jam.index.hour).to_numpy(), index=jam.index)
            if tengah:
                ki = (sebelum[c] - pola[c].reindex(sebelum.index.hour).to_numpy()).iloc[-jam_tepi:].mean()
                ka = (sesudah[c] - pola[c].reindex(sesudah.index.hour).to_numpy()).mean()
                w = np.arange(1, len(jam) + 1) / (len(jam) + 1)
                isi = isi + (1 - w) * ki + w * ka
            era.loc[jam.index, c] = isi
        celah.append((a, b, len(jam), 'tengah' if tengah else 'ujung'))
    return era, celah


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    grib, ztd_csv, kode = sys.argv[1:-2], sys.argv[-2], sys.argv[-1].upper()
    lat, lon, h_st, h_ell = STASIUN[kode]
    z = pd.read_csv(ztd_csv, parse_dates=['waktu_utc']).set_index('waktu_utc').sort_index()
    era, info = meteo_stasiun(grib, kode, z.index.min(), z.index.max())
    for a, b, n, jenis in info['celah']:
        print(f'{kode}: celah ERA5 {a:%d %b %H}–{b:%d %b %H} UTC ({n} jam, {jenis}) diisi -> METEO_ISI')
    e = era[['tekanan_hpa', 'suhu_k']].reindex(era.index.union(z.index)).interpolate('time').reindex(z.index)
    z['tekanan_hpa'], z['suhu_k'] = e.tekanan_hpa, e.suhu_k
    z['sumber_meteo'] = era.sumber_meteo.reindex(z.index.floor('1h')).to_numpy()
    phi = math.radians(lat)
    z['zhd_m'] = 0.0022768 * z.tekanan_hpa / (1 - 0.00266 * math.cos(2 * phi) - 0.00028 * h_ell / 1000)
    z['zwd_m'] = z.ztd_m - z.zhd_m
    z['tm_k'] = 70.2 + 0.72 * z.suhu_k
    pi = 1e6 / (1000.0 * 461.5 * (3739.0 / z.tm_k + 0.221))
    z['pwv_mm'] = z.zwd_m * pi * 1000
    z['sigma_pwv_mm'] = z.sigma_m * pi * 1000
    z.to_csv(f'pwv_30detik_{kode.lower()}.csv')

    g = z.groupby(z.index.floor('30min'))
    s = pd.DataFrame({
        'pwv_mm': g.pwv_mm.mean(), 'sigma_pwv_mm': g.sigma_pwv_mm.mean(),
        'ztd_m': g.ztd_m.mean(), 'zhd_m': g.zhd_m.mean(), 'zwd_m': g.zwd_m.mean(),
        'tekanan_hpa': g.tekanan_hpa.mean(), 'suhu_k': g.suhu_k.mean(), 'tm_k': g.tm_k.mean(),
        'n_epoch': g.size(),
        'sumber_meteo': g.sumber_meteo.agg(lambda v: 'ERA5_ISI' if (v == 'ERA5_ISI').any() else 'ERA5'),
        'produk_orbit': g.produk.agg(lambda v: 'RAPID' if (v == 'COD0OPSRAP').any() else 'MGEX_FINAL'),
        'konv': g.flag.agg(lambda v: (v == 'KONVERGENSI').any()),
    })
    s['flag_kualitas'] = np.select(
        [s.n_epoch < 20, s.konv, s.sumber_meteo == 'ERA5_ISI', s.produk_orbit == 'RAPID'],
        ['CELAH', 'KONVERGENSI', 'METEO_ISI', 'ORBIT_RAPID'], 'OK')
    s = s.drop(columns='konv')
    negatif = s.pwv_mm < 0          # fisik tidak mungkin; muncul di CLBG pagi yang sangat kering (bias nilai mutlak)
    if negatif.any():
        print(f'{kode}: {int(negatif.sum())} slot PWV < 0 dibuang:', list(s.index[negatif].strftime('%Y-%m-%d %H:%M')))
        s = s[~negatif]
    s.insert(0, 'kode_stasiun', kode)
    s.index = s.index.strftime('%Y-%m-%dT%H:%M:%SZ'); s.index.name = 'waktu_utc'
    s['run_id'] = 'pwv-' + pd.Timestamp.now(tz='Asia/Jakarta').strftime('%Y%m%d-%H%M')
    bulat = {'pwv_mm': 2, 'sigma_pwv_mm': 2, 'ztd_m': 4, 'zhd_m': 4, 'zwd_m': 4,
             'tekanan_hpa': 1, 'suhu_k': 1, 'tm_k': 1}
    s.round(bulat).to_csv(f'pwv_30menit_{kode.lower()}.csv')
    print(kode, '| ERA5 sampai', info['era5_terakhir'], '| slot', len(s), '|', s.flag_kualitas.value_counts().to_dict())
    print('PWV mm: min %.1f  median %.1f  maks %.1f | Pi rata2 %.4f | tekanan %.1f–%.1f hPa' % (
        s.pwv_mm.min(), s.pwv_mm.median(), s.pwv_mm.max(), pi.mean(), s.tekanan_hpa.min(), s.tekanan_hpa.max()))


if __name__ == '__main__':
    main()
