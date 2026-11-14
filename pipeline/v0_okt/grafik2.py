"""Grafik hasil uji awal JemurAman: PWV CKRG vs hujan GPM IMERG (waktu WIB)."""
import sys
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker

src, ev_csv, daily_csv, out_png = sys.argv[1:5]
a = pd.read_csv(src, index_col=0, parse_dates=True)
ev = pd.read_csv(ev_csv, parse_dates=['onset_utc'])
dl = pd.read_csv(daily_csv, index_col=0, parse_dates=True)
wib = pd.Timedelta('7h')
a.index = a.index + wib
end = a['hujan_mm_per_jam'].last_valid_index() + pd.Timedelta('30min')
a = a.loc[:end]

SURF, INK, INK2, MUTED, GRID = '#fcfcfb', '#0b0b0b', '#52514e', '#8a8984', '#e4e3df'
BLUE = '#2a78d6'
plt.rcParams.update({'font.size': 10.5, 'axes.edgecolor': GRID, 'axes.labelcolor': INK2,
                     'xtick.color': INK2, 'ytick.color': INK2, 'font.family': 'DejaVu Sans'})
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6.2), sharex=True,
                               gridspec_kw=dict(height_ratios=[2.2, 1], hspace=0.12))
fig.patch.set_facecolor(SURF)
for ax in (ax1, ax2):
    ax.set_facecolor(SURF)
    ax.grid(axis='y', color=GRID, lw=0.8)
    ax.spines[['top', 'right', 'left']].set_visible(False)
    ax.tick_params(length=0)
    for t in ev['onset_utc'] + wib:
        ax.axvline(t, color=MUTED, lw=1, ls=(0, (3, 3)), zorder=1)

# panel atas: PWV
ax1.axhline(45, color=MUTED, lw=1, zorder=1)
ax1.text(a.index[0], 45.8, '45 mm', color=INK2, fontsize=9.5, va='bottom')
ax1.plot(a.index, a['pwv_3jam_mm'], color=BLUE, lw=2, zorder=3, solid_capstyle='round')
for d, row in dl.iterrows():
    s, e = d + wib, d + wib + pd.Timedelta('1D')
    if s > end:
        continue
    e = min(e, end)
    ax1.plot([s, e], [row['pwv_rata2_mm']] * 2, color=INK2, lw=1.2, zorder=2)
ax1.set_ylim(15, 82)
ax1.set_ylabel('PWV (mm)')
ax1.text(pd.Timestamp('2026-10-19 07:00'), 22, 'Kering: rata-rata harian 31–40 mm',
         color=INK2, fontsize=9.5)
ax1.text(pd.Timestamp('2026-10-25 11:00'), 76, 'Basah: 50–60 mm', color=INK2, fontsize=9.5)
ax1.annotate('', xy=(pd.Timestamp('2026-10-24 19:00'), 50.1), xytext=(pd.Timestamp('2026-10-19 19:00'), 30.8),
             arrowprops=dict(arrowstyle='->', color=INK, lw=1.2), zorder=4)
ax1.text(pd.Timestamp('2026-10-21 06:00'), 56, '+19 mm dalam 5 hari\nsebelum hujan pertama',
         color=INK, fontsize=10, ha='center')
ax1.legend(handles=[plt.Line2D([], [], color=BLUE, lw=2, label='PWV, rata-rata bergerak 3 jam'),
                    plt.Line2D([], [], color=INK2, lw=1.2, label='Rata-rata harian (hari UTC)'),
                    plt.Line2D([], [], color=MUTED, lw=1, ls=(0, (3, 3)), label='Awal kejadian hujan')],
           loc='upper left', frameon=False, fontsize=9.5)

# panel bawah: hujan
ax2.bar(a.index, a['hujan_mm_per_jam'], width=0.019, color=BLUE, align='edge', zorder=3)
ax2.set_ylabel('Hujan (mm/jam)')
ax2.set_ylim(0, 14)
ax2.xaxis.set_major_locator(mdates.DayLocator())
ax2.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{mdates.num2date(v).day} Okt"))

fig.text(0.075, 0.965, 'Uap air di atas Karawang naik ±19 mm sebelum hujan pertama musim ini',
         fontsize=14, fontweight='bold', color=INK, ha='left')
fig.text(0.075, 0.93, 'CKRG, 18–28 Okt 2026 (WIB) · PWV: PPP GPS + GLONASS (RTKLIB, orbit CODE, ERA5) · Hujan: IMERG Late Run',
         fontsize=10, color=INK2, ha='left')
fig.text(0.075, 0.012, 'Rata-rata 15 satelit per epoch (9 GPS + 6 GLONASS). 25–28 Okt memakai orbit rapid; tekanan/suhu 27–28 Okt dari pola rata-rata\n'
         'ERA5 18–26 Okt (ERA5 belum terbit). Satu jam pertama tiap hari (konvergensi) tidak ditampilkan.',
         fontsize=8.5, color=MUTED, ha='left', va='bottom')
fig.subplots_adjust(left=0.075, right=0.98, top=0.9, bottom=0.11)
fig.savefig(out_png, dpi=200, facecolor=SURF)
print('ok', out_png)
