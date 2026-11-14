import pandas as pd, numpy as np
df = pd.read_csv('/home/claude/proc2/hasil_pwv_hujan_30menit.csv', index_col=0, parse_dates=True)
p = df['pwv_30min_mm']
pc = p.rolling(2, min_periods=1).mean()            # rata-rata 1 jam ke belakang (kausal)
rain = df['hujan_mm_per_jam']
wib_h = (df.index + pd.Timedelta('7h')).hour
# anomali: PWV dikurangi rata-rata jam yang sama pada 7 hari sebelumnya (kausal)
slot = (df.index.hour*2 + df.index.minute//30)
anom = pd.Series(np.nan, index=df.index)
for i, t in enumerate(df.index):
    prev = pc[(df.index < t - pd.Timedelta('12h')) & (df.index >= t - pd.Timedelta('7D')) & (slot == slot[i])]
    if len(prev) >= 3: anom.iloc[i] = pc.iloc[i] - prev.mean()
d3 = pc - pc.shift(6)                               # kenaikan 3 jam ke belakang
wet = rain >= 1.0
# observasi "hujan dalam 3 jam ke depan" (t, t+3h]
fut = pd.Series([bool(wet.iloc[i+1:i+7].any()) if i+6 < len(wet) else np.nan for i in range(len(wet))], index=df.index)
# awal hujan
on = [rain.index[i] for i in range(6, len(rain)) if rain.iloc[i] >= 1 and (rain.iloc[i-6:i] < 0.2).all()]
pers = wet.shift(48).fillna(False) | wet.shift(47).fillna(False) | wet.shift(49).fillna(False)
rules = {
 'Ambang tetap PWV ≥ 45 mm': pc >= 45,
 'Pola harian: tiap 13.00–17.00 WIB': pd.Series((wib_h >= 13) & (wib_h < 17), index=df.index),
 'Persistensi: hujan kemarin jam ini': pers,
 'Kenaikan ΔPWV ≥ 4 mm/3 jam': d3 >= 4,
 'Anomali ≥ 5 mm': anom >= 5,
 'Anomali ≥ 3 mm dan ΔPWV ≥ 3 mm/3 jam': (anom >= 3) & (d3 >= 3),
}
def skor(a, b, c, dd):
    n = a+b+c+dd; pod = a/(a+c) if a+c else np.nan; far = b/(a+b) if a+b else np.nan
    csi = a/(a+b+c) if a+b+c else np.nan
    hss = 2*(a*dd-b*c)/((a+c)*(c+dd)+(a+b)*(b+dd)) if n else np.nan
    return pod, far, csi, hss
rows=[]
valid = fut.notna() & pc.notna() & anom.notna()   # periode dengan anomali tersedia (mulai ~21 Okt)
for name, al in rules.items():
    al = al.fillna(False).astype(bool)
    for lab, m in (('semua', valid), ('siang', valid & pd.Series((wib_h>=6)&(wib_h<18), index=df.index))):
        f = al[m]; o = fut[m].astype(bool)
        a=int((f&o).sum()); b=int((f&~o).sum()); c=int((~f&o).sum()); dd=int((~f&~o).sum())
        pod,far,csi,hss = skor(a,b,c,dd)
        rows.append(dict(aturan=name, jam=lab, n=a+b+c+dd, hit=a, alarm_palsu=b, terlewat=c, benar_negatif=dd, nyala_pct=100*(a+b)/(a+b+c+dd), POD=pod, FAR=far, CSI=csi, HSS=hss))
    # per kejadian: peringatan (awal episode) dalam 0–3 jam sebelum onset
    starts = al[al & ~al.shift(1, fill_value=False)].index
    hits=[]; leads=[]
    for t in on:
        if anom.get(t) is np.nan: pass
        w = starts[(starts <= t) & (starts >= t - pd.Timedelta('3h'))]
        on_now = bool(al.get(t, False)) or bool(al.get(t - pd.Timedelta('30min'), False))
        if len(w): hits.append(1); leads.append((t - w.min()).total_seconds()/60)
        else: hits.append(0)
    fa = sum(1 for s in starts if not wet[(wet.index > s) & (wet.index <= s + pd.Timedelta('3h'))].any())
    rows[-1].update(dict(onset_tertangkap=f'{sum(hits)}/{len(on)}', lead_median_min=np.median(leads) if leads else np.nan, peringatan_dikirim=len(starts), peringatan_palsu=fa))
r = pd.DataFrame(rows)
pd.set_option('display.width', 250)
print(r.round(2).to_string())
print('periode valid:', valid[valid].index.min(), valid[valid].index.max(), 'onset:', on)
# confusion matrix per slot sederhana (hujan di slot yang sama) untuk ambang 45, seluruh periode
m = pc.notna() & rain.notna(); f = (pc>=45)[m]; o = wet[m]
print('slot-sama 45mm: hit',int((f&o).sum()),'FA',int((f&~o).sum()),'miss',int((~f&o).sum()),'CN',int((~f&~o).sum()), 'nyala %.0f%%'%(100*f.mean()), skor(int((f&o).sum()),int((f&~o).sum()),int((~f&o).sum()),int((~f&~o).sum())))
r.to_csv('metrik_aturan.csv', index=False)
pd.DataFrame({'pwv':pc,'anom':anom,'d3':d3,'hujan':rain,'hujan_3jam_depan':fut}).to_csv('fitur.csv')
