"""Grafik satu replay: PWV 1 jam, ambang persentil, status BERPOTENSI, notifikasi, dan hujan IMERG.

python pipeline/evaluasi/grafik_replay.py LOG_REPLAY KODE "2026-10-24 00:00" "2026-10-26 00:00" keluar.png
LOG_REPLAY = folder hasil `replay.py --ekspor` (sesiN_status.csv, sesiN_pesan.csv).
"""
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AKAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(AKAR))
import yaml  # noqa: E402
from mesin.fitur import seri_layak  # noqa: E402

TEKS, SEKUNDER, GARIS, GRID = '#1f1f1e', '#5f5e5a', '#bdbcb5', '#e6e5e0'
BIRU, OREN, HUJAN = '#2a78d6', '#eb6834', '#6b6a64'


def ambang_persentil(pwv1, p, W, mulai, selesai):
    """Nilai PWV yang harus dilampaui agar persentil >= p (definisi sama dengan mesin/fitur.py)."""
    out = {}
    for t in pwv1[mulai:selesai].index:
        ref = pwv1[t - pd.Timedelta(days=W):t - pd.Timedelta(hours=12)]
        ref = np.sort(ref[:-1].dropna().to_numpy()) if len(ref) else np.array([])
        out[t] = ref[math.ceil(p / 100 * len(ref)) - 1] if len(ref) else np.nan
    return pd.Series(out)


def main(log, kode, mulai_wib, selesai_wib, keluar):
    log = Path(log)
    st = pd.read_csv(next(log.glob('*_status.csv'))); ps = pd.read_csv(next(log.glob('*_pesan.csv')))
    st = st[st.kode_stasiun == kode].copy(); st['w'] = pd.to_datetime(st.waktu_wib)
    m0, m1 = pd.Timestamp(mulai_wib), pd.Timestamp(selesai_wib)
    st = st[(st.w >= m0) & (st.w <= m1)]
    a = yaml.safe_load(open(AKAR / 'config' / 'aturan.yaml', encoding='utf-8'))
    p2, W = a['level2']['min'], a['fitur']['jendela_acuan_hari']

    pwv = pd.read_csv(AKAR / 'data' / 'pwv' / f'pwv_30menit_{kode.lower()}.csv', parse_dates=['waktu_utc'])
    v = seri_layak(pwv)
    v.index = v.index.tz_convert('Asia/Jakarta').tz_localize(None)
    sebelum = v.shift(1); pwv1 = ((v + sebelum) / 2).fillna(v).fillna(sebelum)
    # status pada tau = akhir slot; garis PWV digambar di tau juga
    pwv1.index = pwv1.index + pd.Timedelta(minutes=30)
    thr = ambang_persentil(pwv1, p2, W, m0, m1)

    h = pd.read_csv(AKAR / 'data' / 'hujan' / 'hujan_30menit.csv', parse_dates=['waktu_utc'])
    h = h[h.kode_stasiun == kode].copy()
    h['w'] = h.waktu_utc.dt.tz_convert('Asia/Jakarta').dt.tz_localize(None)
    h = h[(h.w >= m0) & (h.w < m1)]
    aw = pd.read_csv(AKAR / 'data' / 'hujan' / 'awal_hujan.csv')
    aw = pd.to_datetime(aw[aw.kode_stasiun == kode].jam_wib)
    aw = aw[(aw >= m0) & (aw < m1)]

    ps['w'] = pd.to_datetime(ps.dijadwalkan_wib)
    kirim = ps[(ps.status == 'TERKIRIM') & ps.jenis.isin(['BERPOTENSI', 'AMAN_LAGI']) & (ps.w >= m0) & (ps.w <= m1)]
    tahan = ps[(ps.status == 'DITAHAN') & (ps.jenis == 'AMAN_LAGI') & (ps.alasan == 'LEWAT_JAM_JEMUR')
               & (ps.w >= m0) & (ps.w <= m1)]

    fig, (ax, bx) = plt.subplots(2, 1, figsize=(7.2, 3.6), sharex=True, gridspec_kw=dict(height_ratios=[2.3, 1], hspace=0.08))
    on = (st.level == 'BERPOTENSI').to_numpy(); t = st.w.to_numpy()
    for i in np.flatnonzero(on):
        for z in (ax, bx):
            z.axvspan(t[i] - np.timedelta64(30, 'm'), t[i], color=OREN, alpha=0.13, lw=0)
    for z in (ax, bx):
        for d in pd.date_range(m0.normalize(), m1, freq='D'):
            j0, j1 = d + pd.Timedelta(hours=6), d + pd.Timedelta(hours=18)
            z.axvline(j0, color=GARIS, lw=0.6, ls=':'); z.axvline(j1, color=GARIS, lw=0.6, ls=':')
    s = pwv1[m0:m1]
    ax.plot(s.index, s.to_numpy(), color=BIRU, lw=2, label='PWV 1 jam (CKRG)')
    ax.plot(thr.index, thr.to_numpy(), color=SEKUNDER, lw=1.2, ls='--', label=f'ambang persentil {p2:g} (15 hari terakhir)')
    ytop = np.nanmax(s.to_numpy()) + 6
    for _, r in kirim.iterrows():
        jenis = 'notifikasi "Berpotensi hujan"' if r.jenis == 'BERPOTENSI' else 'notifikasi "aman lagi"'
        c = OREN if r.jenis == 'BERPOTENSI' else BIRU
        ax.annotate('', xy=(r.w, ytop - 4.2), xytext=(r.w, ytop - 0.6),
                    arrowprops=dict(arrowstyle='-|>', color=c, lw=1.4, mutation_scale=9))
        ax.text(r.w, ytop + 0.3, f'{r.w:%H.%M}', ha='center', va='bottom', fontsize=7.5, color=TEKS)
    for _, r in tahan.iterrows():
        ax.annotate('', xy=(r.w, ytop - 4.2), xytext=(r.w, ytop - 0.6),
                    arrowprops=dict(arrowstyle='-|>', color=GARIS, lw=1.4, mutation_scale=9, ls=(0, (2, 1.5))))
        ax.text(r.w, ytop + 0.3, f'{r.w:%H.%M}', ha='center', va='bottom', fontsize=7.5, color=SEKUNDER)
    ax.set_ylim(np.nanmin(s.to_numpy()) - 11, ytop + 4.5)
    ax.set_ylabel('PWV (mm)', fontsize=8, color=SEKUNDER)
    from matplotlib.lines import Line2D
    hd, lb = ax.get_legend_handles_labels()
    hd += [Line2D([], [], marker='v', color=OREN, ls='None', ms=6)]
    lb += ['notifikasi "Berpotensi hujan"']
    if len(kirim[kirim.jenis == 'AMAN_LAGI']):
        hd.append(Line2D([], [], marker='v', color=BIRU, ls='None', ms=6)); lb.append('notifikasi "aman lagi"')
    if len(tahan):
        hd.append(Line2D([], [], marker='v', color=GARIS, ls='None', ms=6))
        lb.append('"aman lagi" ditahan (sesudah 15.00)')
    ax.legend(hd, lb, loc='lower left', fontsize=7, frameon=False, ncol=2, handlelength=2.2, columnspacing=1.4)

    bx.bar(h.w + pd.Timedelta(minutes=15), h.hujan_mm_per_jam, width=0.019, color=HUJAN)
    bx.axhline(1.0, color=GARIS, lw=0.8, ls='--')
    for x in aw:
        bx.annotate(f'awal hujan {x:%H.%M}', xy=(x, 2.4), xytext=(x + pd.Timedelta(hours=1.2), 4.2), fontsize=7.5,
                    color=TEKS, arrowprops=dict(arrowstyle='-', color=SEKUNDER, lw=0.7), va='center')
    bx.set_ylim(0, max(5.5, h.hujan_mm_per_jam.max() * 1.15))
    bx.set_ylabel('Hujan\n(mm/jam)', fontsize=8, color=SEKUNDER)
    bx.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
    bx.xaxis.set_major_formatter(mdates.DateFormatter('%H.%M'))
    for d in pd.date_range(m0.normalize(), m1 - pd.Timedelta(hours=1), freq='D'):
        bx.text(d + pd.Timedelta(hours=12), -0.47, f'{d.day} Okt', transform=bx.get_xaxis_transform(),
                ha='center', fontsize=8, color=TEKS)
    for z in (ax, bx):
        for k in ('top', 'right'): z.spines[k].set_visible(False)
        for k in ('left', 'bottom'): z.spines[k].set_color(GARIS)
        z.tick_params(colors=SEKUNDER, labelsize=7.5); z.grid(axis='y', color=GRID, lw=0.6); z.set_axisbelow(True)
    bx.set_xlim(m0, m1)
    fig.text(0.01, -0.06, 'Arsiran oranye = status "Berpotensi hujan". Garis titik = jam notifikasi 06.00–18.00 WIB. '
             'Sumber hujan: GPM IMERG.', fontsize=7, color=SEKUNDER)
    fig.savefig(keluar, dpi=300, bbox_inches='tight', facecolor='white')
    print(keluar)


if __name__ == '__main__':
    main(*sys.argv[1:6])
