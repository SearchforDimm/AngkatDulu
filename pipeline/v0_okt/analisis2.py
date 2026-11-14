import pandas as pd, numpy as np
z = pd.read_csv('pwv_gr_30detik.csv', index_col=0, parse_dates=True)
r = pd.read_csv('/home/claude/data_in/extracted/ANGKATDULU/GIOVANNi/g4.areaAvgTimeSeries.GPM_3IMERGHHL_07_precipitation.20261018-20261028.107E_6S_107E_6S.csv', skiprows=8)
r.columns = ['time', 'rain']; r['time'] = pd.to_datetime(r['time']); r = r.set_index('time')['rain'].where(lambda s: s > -999)
pw30 = z['pwv_mm'].resample('30min').mean()
df = pd.DataFrame({'pwv_30min_mm': pw30, 'pwv_3jam_mm': pw30.rolling(6, center=True, min_periods=3).mean()}).join(r.rename('hujan_mm_per_jam'), how='outer')
df = df.loc['2026-10-18 01:00':'2026-10-28 23:30']
rain = df['hujan_mm_per_jam']
ev = []
for i in range(6, len(rain)):
    if rain.iloc[i] >= 1.0 and (rain.iloc[i-6:i] < 0.2).all():
        t = rain.index[i]; p0 = df['pwv_3jam_mm'].get(t)
        row = dict(onset_utc=t, onset_wib=t + pd.Timedelta('7h'), hujan_mm_per_jam=rain[t], pwv_saat_onset=p0)
        for h in (1, 3, 6):
            pb = df['pwv_3jam_mm'].get(t - pd.Timedelta(f'{h}h')); row[f'naik_{h}jam_mm'] = None if pb is None or pd.isna(pb) else p0 - pb
        ev.append(row)
ev = pd.DataFrame(ev); print(ev.round(1).to_string())
d = df.dropna(subset=['hujan_mm_per_jam', 'pwv_3jam_mm']); wet = d['hujan_mm_per_jam'] >= 1
for th in (45, 50):
    hi = d['pwv_3jam_mm'] >= th
    print(f'ambang {th}: slot hujan {int(wet.sum())}, saat PWV>=ambang {int((wet&hi).sum())} | slot PWV>=ambang {int(hi.sum())}, yang hujan {int((hi&wet).sum())} ({(hi&wet).sum()/hi.sum()*100:.0f}%)')
daily = pd.DataFrame({'pwv_rata2_mm': df['pwv_30min_mm'].resample('1D').mean(), 'hujan_mm': (df['hujan_mm_per_jam']*0.5).resample('1D').sum(min_count=1)})
print(daily.round(1).to_string())
df.to_csv('hasil_pwv_hujan_30menit.csv', float_format='%.2f'); ev.to_csv('hasil_kejadian_hujan.csv', index=False, float_format='%.2f'); daily.to_csv('hasil_harian.csv', float_format='%.2f')
