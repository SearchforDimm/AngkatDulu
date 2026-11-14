"""ZTD (RTKLIB PPP-fixed GPS+GLONASS) -> PWV dengan tekanan & suhu ERA5."""
import numpy as np, pandas as pd, math, grib1
LAT, LON = -6.11119, 107.32804
H_MSL = 5.0            # perkiraan tinggi ortometrik CKRG (m), asumsi
m = grib1.read('era5_18_26.grib')
rows = {}
for x in m:
    v = x['vals']; lats, lons = x['lats'], x['lons']
    if x['param'] == 134:   # tekanan: pakai baris utara (titik laut, setara permukaan laut), interpolasi bujur
        w = (LON - lons[0]) / (lons[1] - lons[0]); val = (v[0, 0] * (1 - w) + v[0, 1] * w) / 100.0
    else:                   # suhu 2 m: bilinear 4 titik
        wy = (LAT - lats[0]) / (lats[1] - lats[0]); wx = (LON - lons[0]) / (lons[1] - lons[0])
        val = (v[0, 0]*(1-wx)*(1-wy) + v[0, 1]*wx*(1-wy) + v[1, 0]*(1-wx)*wy + v[1, 1]*wx*wy)
    rows.setdefault(x['time'], {})['p' if x['param'] == 134 else 't'] = val
era = pd.DataFrame(rows).T; era.index = pd.to_datetime(era.index); era = era.sort_index()
era['p'] = era['p'] * np.exp(-9.80665 * H_MSL / (287.05 * era['t']))   # koreksi ke tinggi stasiun
# isi 27-28 Okt (ERA5 belum terbit) dengan rata-rata per jam 18-26 Okt -> ditandai
idx = pd.date_range('2026-10-18', '2026-10-29', freq='1h', inclusive='left')
clim = era.groupby(era.index.hour).mean()
era = era.reindex(idx); era['sumber'] = np.where(era['p'].isna(), 'pola rata-rata 18-26 Okt (asumsi)', 'ERA5')
for c in ('p', 't'):
    era[c] = era[c].fillna(pd.Series(clim[c].reindex(era.index.hour).to_numpy(), index=era.index))
# ZTD per 30 detik
z = pd.read_csv('run/ztd_gr_semua.csv', parse_dates=['time_gpst'])
zs = []
for doy in range(291, 302):
    r = [l.strip().split(',') for l in open(f'run/out/ckrg{doy}_fix_gr.pos.stat') if l.startswith('$TROP')]
    for x in r:
        zs.append((pd.Timestamp('1980-01-06') + pd.Timedelta(seconds=int(x[1])*604800 + float(x[2]) - 18), float(x[5]), float(x[6]), float(x[2]) % 86400))
z = pd.DataFrame(zs, columns=['time_utc', 'ztd', 'sig', 'sod']).set_index('time_utc')
z = z[z['sod'] >= 3600]                 # buang 1 jam konvergensi tiap hari
e = era[['p', 't']].reindex(z.index.union(era.index)).interpolate('time').reindex(z.index)
lat = math.radians(LAT)
z['p_hpa'] = e['p']; z['t_k'] = e['t']
z['zhd'] = 0.0022768 * z['p_hpa'] / (1 - 0.00266 * math.cos(2 * lat) - 0.00028 * 27.6 / 1000)
z['zwd'] = z['ztd'] - z['zhd']
tm = 70.2 + 0.72 * z['t_k']
pi = 1e6 / (1000.0 * 461.5 * (3739.0 / tm + 0.221))
z['pi'] = pi; z['pwv_mm'] = z['zwd'] * pi * 1000; z['sig_pwv_mm'] = z['sig'] * pi * 1000
z['sumber_meteo'] = era['sumber'].reindex(z.index.floor('1h')).to_numpy()
z.to_csv('pwv_gr_30detik.csv')
pw30 = z['pwv_mm'].resample('30min').mean()
print('Pi rata2', round(z['pi'].mean(), 4), '| ZHD', round(z['zhd'].min(), 4), '-', round(z['zhd'].max(), 4))
d = pd.DataFrame({'pwv': z['pwv_mm'].resample('1D').mean(), 'min': z['pwv_mm'].resample('1D').min(), 'maks': z['pwv_mm'].resample('1D').max(), 'p': z['p_hpa'].resample('1D').mean()})
print(d.round(1).to_string())
