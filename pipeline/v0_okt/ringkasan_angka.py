"""Satu skrip untuk SEMUA angka yang dikutip di proposal AngkatDulu.
Jalankan: python3 ringkasan_angka.py  -> mencetak tabel ringkasan & menulis ringkasan_angka.md/.csv
Pembulatan: metrik skill 2 desimal (ROUND_HALF_UP); mm 1 desimal; persen bilangan bulat."""
import math, numpy as np, pandas as pd
from decimal import Decimal, ROUND_HALF_UP
RUN = '/home/claude/proc2/run'; P2 = '/home/claude/proc2'
def r(x, nd=2):
    if x is None or (isinstance(x, float) and math.isnan(x)): return 'n/a'
    return str(Decimal(str(x)).quantize(Decimal(1).scaleb(-nd), rounding=ROUND_HALF_UP)).replace('.', ',')
def pct(x): return r(100*x, 0) + '%'
out = []   # (kode, besaran, nilai, keterangan)
def add(kode, besaran, nilai, ket=''): out.append((kode, besaran, nilai, ket))

# ---------- 1. PPP: GPS saja vs GPS+GLONASS (konfigurasi PPP-fixed yang dipakai untuk PWV)
ns = {'g': [], 'gr': []}; sg = {'g': [], 'gr': []}
for doy in range(291, 302):
    for c in ('g', 'gr'):
        pos = [l.split() for l in open(f'{RUN}/out/ckrg{doy}_fix_{c}.pos') if not l.startswith('%')]
        ns[c] += [int(x[6]) for x in pos]
        tr = [l.strip().split(',') for l in open(f'{RUN}/out/ckrg{doy}_fix_{c}.pos.stat') if l.startswith('$TROP')]
        tow = np.array([float(x[2]) for x in tr]); s = np.array([float(x[6]) for x in tr])
        sg[c] += list(s[tow >= tow.min() + 3600] * 1000)
add('PPP', 'Satelit per epoch, GPS saja', r(np.mean(ns['g']), 1), '18–28 Okt, PPP-fixed harian')
add('PPP', 'Satelit per epoch, GPS + GLONASS', r(np.mean(ns['gr']), 1), '18–28 Okt, PPP-fixed harian')
add('PPP', 'Sigma ZTD, GPS saja (mm)', r(np.mean(sg['g']), 1), 'rata-rata setelah 1 jam pertama tiap hari')
add('PPP', 'Sigma ZTD, GPS + GLONASS (mm)', r(np.mean(sg['gr']), 1), 'idem')

# ---------- 2. PWV harian dan sensitivitas meteorologi
z = pd.read_csv(f'{P2}/pwv_gr_30detik.csv', index_col=0, parse_dates=True)
d = z['pwv_mm'].resample('1D').mean()
for t in ('2026-10-19', '2026-10-24', '2026-10-27'): add('PWV', f'PWV rata-rata harian {t[8:]} Okt (mm)', r(d[t], 1), 'hari UTC')
add('PWV', 'Kenaikan 19→24 Okt (mm)', r(d['2026-10-24'] - d['2026-10-19'], 1), '')
ze = z[z['sumber_meteo'] == 'ERA5']; lat = math.radians(-6.11119)
zhd = 0.0022768 * ze['p_hpa'].mean() / (1 - 0.00266 * math.cos(2 * lat) - 0.00028 * 27.6 / 1000)
tm = 70.2 + 0.72 * ze['t_k'].mean(); pi = 1e6 / (1000 * 461.5 * (3739 / tm + 0.221))
dd = ((ze['ztd'] - zhd) * pi * 1000 - ze['pwv_mm']).resample('30min').mean().dropna()
add('SENS', 'Selisih PWV, met. konstan vs ERA5: RMS (mm)', r(float(np.sqrt((dd**2).mean()))), 'meniru model empiris tanpa variasi harian')
add('SENS', 'Selisih PWV, met. konstan vs ERA5: maks (mm)', r(float(dd.abs().max())), '')

# ---------- 3. Evaluasi peringatan
df = pd.read_csv(f'{P2}/hasil_pwv_hujan_30menit.csv', index_col=0, parse_dates=True)
pc = df['pwv_30min_mm'].rolling(2, min_periods=1).mean()      # rata-rata 1 jam ke belakang (kausal)
rain = df['hujan_mm_per_jam']; wet = rain >= 1.0
wib = df.index + pd.Timedelta('7h'); slot = df.index.hour * 2 + df.index.minute // 30
anom = pd.Series(np.nan, index=df.index)
for i, t in enumerate(df.index):
    prev = pc[(df.index < t - pd.Timedelta('12h')) & (df.index >= t - pd.Timedelta('7D')) & (slot == slot[i])]
    if len(prev) >= 3: anom.iloc[i] = pc.iloc[i] - prev.mean()
d3 = pc - pc.shift(6)
fut = pd.Series([bool(wet.iloc[i+1:i+7].any()) if i + 6 < len(wet) else np.nan for i in range(len(wet))], index=df.index)
pers = wet.shift(47, fill_value=False) | wet.shift(48, fill_value=False) | wet.shift(49, fill_value=False)
rules = {'Ambang tetap PWV ≥ 45 mm': pc >= 45,
         'Anomali PWV ≥ 5 mm': anom >= 5,
         'Kenaikan ΔPWV ≥ 4 mm/3 jam': d3 >= 4,
         'Baseline pola harian (13.00–17.00 WIB)': pd.Series((wib.hour >= 13) & (wib.hour < 17), index=df.index),
         'Baseline persistensi (hujan kemarin)': pers}
def tab(f, o):
    a = int((f & o).sum()); b = int((f & ~o).sum()); c = int((~f & o).sum()); e = int((~f & ~o).sum()); return a, b, c, e
def skor(a, b, c, e):
    pod = a / (a + c); far = b / (a + b) if a + b else float('nan'); csi = a / (a + b + c)
    hss = 2 * (a * e - b * c) / ((a + c) * (c + e) + (a + b) * (b + e)); return pod, far, csi, hss
# S-45: serentak, 18–28 Okt
m = pc.notna() & rain.notna(); a, b, c, e = tab((pc >= 45)[m], wet[m]); pod, far, csi, hss = skor(a, b, c, e)
add('S-45', 'Tabel kontingensi H/F/M/CN', f'{a}/{b}/{c}/{e}', 'slot 30 menit serentak, 18–28 Okt')
add('S-45', 'Waktu menyala', pct((a + b) / (a + b + c + e)), '')
for k, v in zip(('POD', 'FAR', 'CSI', 'HSS'), (pod, far, csi, hss)): add('S-45', k, r(v), '')
on24 = (pc[wib >= pd.Timestamp('2026-10-24')] >= 45).mean()
add('S-45', 'Waktu menyala 24–28 Okt WIB', pct(on24), 'bukti ambang tetap mendeteksi musim lembap')
# P-3J dan E-3J
valid = fut.notna() & pc.notna() & anom.notna()
per = f"{(valid[valid].index.min()+pd.Timedelta('7h')):%d %b %H:%M}–{(valid[valid].index.max()+pd.Timedelta('7h')):%d %b %H:%M} WIB"
onsets = [rain.index[i] for i in range(6, len(rain)) if rain.iloc[i] >= 1 and (rain.iloc[i-6:i] < 0.2).all()]
onsets = [t for t in onsets if valid.get(t, False) or anom.notna().get(t, False)]
tabP = {}
for name, al in rules.items():
    al = al.fillna(False).astype(bool)
    a, b, c, e = tab(al[valid], fut[valid].astype(bool)); tabP[name] = (a, b, c, e); pod, far, csi, hss = skor(a, b, c, e)
    add('P-3J', f'{name}: waktu menyala', pct((a + b) / (a + b + c + e)), per)
    for k, v in zip(('POD', 'FAR', 'CSI', 'HSS'), (pod, far, csi, hss)): add('P-3J', f'{name}: {k}', r(v), '')
    starts = al[al & ~al.shift(1, fill_value=False)].index
    hit, lead = 0, []
    for t in onsets:
        w = starts[(starts <= t) & (starts >= t - pd.Timedelta('3h'))]
        if len(w): hit += 1; lead.append((t - w.min()).total_seconds() / 60)
    add('E-3J', f'{name}: awal hujan diperingatkan', f'{hit}/{len(onsets)}', 'peringatan baru 0–3 jam sebelum awal hujan')
    add('E-3J', f'{name}: lead time median (menit)', r(float(np.median(lead)), 0) if lead else 'n/a', '')
add('E-3J', 'Jumlah awal hujan', str(len(onsets)), '≥ 1 mm/jam setelah ≥ 3 jam < 0,2 mm/jam')
# ---------- 4. Nilai ekonomi relatif V (Richardson, 2000) untuk P-3J ambang 45 mm
a, b, c, e = tabP['Ambang tetap PWV ≥ 45 mm']; n = a + b + c + e; sb = (a + c) / n
al = np.linspace(0.005, 0.995, 199)
V = np.array([(min(x, sb) - ((a + b) / n) * x - c / n) / (min(x, sb) - sb * x) for x in al])
pos_ = al[V > 0]
add('V', 'Rentang C/L dengan V > 0', f'{r(pos_.min())}–{r(pos_.max())}' if len(pos_) else 'tidak ada', 'P-3J ambang 45 mm')
add('V', 'V maksimum', r(V.max()), f'pada C/L ≈ {r(al[V.argmax()])}')
add('V', 'Frekuensi dasar hujan 3 jam (s̄)', r(sb), '')
# ---------- 5. Ekonomi
Q_gkp, Q_gkg = 71.95e6, 60.21e6; s = 0.0359; P_gkp, P_gkg = 6500, 8000
add('EKO', 'K_nasional basis GKP (Rp triliun)', r(Q_gkp * 1000 * s * P_gkp / 1e12, 1), 'Q × j × s × P, j = 1 (batas atas)')
add('EKO', 'K_nasional basis GKG (Rp triliun)', r(Q_gkg * 1000 * s * P_gkg / 1e12, 1), 'harga GKG Rp8.000/kg')
yld = Q_gkp / 11.32e6; kp = 0.5 * yld * 1000 * s
add('EKO', 'Susut per petani 0,5 ha per panen (kg)', r(kp, 0), f'produktivitas {r(yld,2)} t GKP/ha')
add('EKO', 'Susut per petani 0,5 ha per panen (Rp ribu)', r(kp * P_gkp / 1000, 0), '')
for rr in (0.25, 0.5):
    add('EKO', f'K_terhindar per 1.000 pengguna per panen, r = {rr}, e = 0,2 (Rp juta)', r(1000 * kp * P_gkp * rr * 0.2 / 1e6, 0), 'asumsi ilustratif; u = 1 untuk pengguna pilot')
res = pd.DataFrame(out, columns=['kode', 'besaran', 'nilai', 'keterangan'])
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 70)
print(res.to_string(index=False))
res.to_csv('/home/claude/proc3/ringkasan_angka.csv', index=False)
open('/home/claude/proc3/ringkasan_angka.md', 'w').write(res.to_markdown(index=False))
