"""Grafik QC: PWV 30 menit dan hujan IMERG per stasiun, 1 Sep–1 Nov 2026 (waktu WIB)."""
import sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.ticker
import matplotlib.pyplot as plt, matplotlib.dates as mdates
import pandas as pd

WARNA = {'CKRG': '#2a78d6', 'BAKO': '#eb6834', 'CLBG': '#1baf7a', 'CJUR': '#c98500'}
TEKS, SEKUNDER, GRID, HUJAN = '#1f1f1e', '#5f5e5a', '#e6e5e0', '#6b6a64'


def imerg(path):
    baris = open(path).read().splitlines()
    k = next(i for i, l in enumerate(baris) if l.startswith('time'))
    d = pd.read_csv(path, skiprows=k + 1, names=['t', 'mm'])
    d['t'] = pd.to_datetime(d.t, format='%Y-%m-%d %H:%M:%S')
    d = d[d.mm > -9000].set_index('t').mm
    d.index = d.index + pd.Timedelta(hours=7)
    return d


def main(pasangan, keluar):
    fig, ax = plt.subplots(2 * len(pasangan), 1, figsize=(12, 2.6 * len(pasangan) + 0.6), sharex=True,
                           gridspec_kw={'height_ratios': [3, 1.2] * len(pasangan), 'hspace': 0.12})
    for k, (kode, f_pwv, f_hujan) in enumerate(pasangan):
        p = pd.read_csv(f_pwv, index_col=0, parse_dates=True)
        p.index = p.index.tz_localize(None) + pd.Timedelta(hours=7)
        ok = p[p.flag_kualitas.isin(['OK', 'METEO_ISI', 'ORBIT_RAPID'])].pwv_mm
        ok = ok.reindex(pd.date_range(ok.index.min(), ok.index.max(), freq='30min'))   # celah tampil putus
        a, b = ax[2 * k], ax[2 * k + 1]
        a.plot(ok.index, ok, color=WARNA[kode], lw=1.0)
        a.set_ylabel('PWV (mm)', color=SEKUNDER, fontsize=9)
        a.text(0.005, 0.93, f'{kode}: PWV 30 menit', transform=a.transAxes, fontsize=10, color=TEKS,
               fontweight='bold', va='top')
        isi = p[p.sumber_meteo == 'ERA5_ISI']
        if len(isi):
            a.axvspan(isi.index.min(), isi.index.max(), color=GRID, alpha=0.6, lw=0)
            a.text(isi.index.min(), 0.03, ' meteo diisi pola\n (ERA5 belum terbit)', fontsize=7.5, color=SEKUNDER,
                   va='bottom', ha='right', transform=a.get_xaxis_transform())
        h = imerg(f_hujan)
        b.bar(h.index, h.values, width=1 / 48, color=HUJAN, lw=0)
        b.set_ylabel('hujan\n(mm/jam)', color=SEKUNDER, fontsize=8)
        for s in (a, b):
            s.grid(axis='y', color=GRID, lw=0.6); s.set_axisbelow(True)
            for sp in ('top', 'right'): s.spines[sp].set_visible(False)
            for sp in ('left', 'bottom'): s.spines[sp].set_color('#bdbcb5')
            s.tick_params(colors=SEKUNDER, labelsize=8)
    ax[-1].xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 8, 15, 22]))
    bulan = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']
    ax[-1].xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda x, _: f'{mdates.num2date(x).day:02d} {bulan[mdates.num2date(x).month - 1]}'))
    fig.suptitle('PWV GNSS dan hujan IMERG, 1 Sep–1 Nov 2026 (WIB)', x=0.06, ha='left', fontsize=12, color=TEKS)
    fig.text(0.06, 0.005, 'Bagian kosong = RINEX tidak ada atau slot konvergensi. Hujan: IMERG Late Run v07, 30 menit.',
             fontsize=8, color=SEKUNDER)
    fig.savefig(keluar, dpi=130, bbox_inches='tight', facecolor='white')


if __name__ == '__main__':
    a = sys.argv[1:]
    main([(a[i], a[i + 1], a[i + 2]) for i in range(0, len(a) - 1, 3)], a[-1])
