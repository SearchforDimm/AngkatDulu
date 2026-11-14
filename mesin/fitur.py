"""Fitur kausal PWV. Satu-satunya definisi fitur: dipakai mesin (per tick) dan kalibrasi (sekaligus).

Slot t = slot 30 menit yang dimulai pada t. Keputusan dibuat di akhir slot (t + 30 menit) dan
hanya memakai slot <= t.
  pwv_1jam  = rata-rata PWV layak slot t-30 menit dan t
  anomali   = pwv_1jam(t) - rata-rata pwv_1jam pada slot jam yang sama, W hari sebelumnya (min 3 hari)
  persentil = peringkat pwv_1jam(t) di antara pwv_1jam [t - W hari, t - 12 jam) (0-100, min 3 hari)
  delta_3j  = pwv_1jam(t) - pwv_1jam(t - 3 jam)
Pembanding (anomali, persentil) dimulai ulang pada tanggal `reset` (mis. setelah ganti antena).
"""
import numpy as np
import pandas as pd

PAKAI = ('OK', 'METEO_ISI', 'ORBIT_RAPID')
SLOT_PER_HARI = 48
HARI = pd.Timedelta(days=1)


def seri_layak(df, mulai=None, akhir=None):
    """df: kolom waktu_utc (UTC), pwv_mm, flag_kualitas -> Series PWV layak di grid 30 menit kontinu.
    Slot tanpa data atau dengan flag KONVERGENSI/CELAH menjadi NaN."""
    layak = df[df.flag_kualitas.isin(PAKAI)]
    s = layak.set_index('waktu_utc').pwv_mm.astype(float)
    mulai = df.waktu_utc.min() if mulai is None else mulai
    akhir = df.waktu_utc.max() if akhir is None else akhir
    return s.reindex(pd.date_range(mulai, akhir, freq='30min'))


def _anomali(pwv1, W, min_hari, reset):
    idx = pwv1.index
    tab = pd.DataFrame({'x': pwv1.to_numpy(), 'hari': idx.normalize(), 'slot': idx.hour * 2 + idx.minute // 30})
    piv = tab.pivot(index='hari', columns='slot', values='x')
    acuan = pd.DataFrame(np.nan, index=piv.index, columns=piv.columns)
    batas = [(None, reset), (reset, None)] if reset is not None else [(None, None)]
    for a, b in batas:
        m = np.ones(len(piv), bool)
        if a is not None: m &= piv.index >= a
        if b is not None: m &= piv.index < b
        if m.any():
            acuan.loc[m] = piv[m].shift(1).rolling(W, min_periods=min_hari).mean().to_numpy()
    nilai_acuan = acuan.stack(future_stack=True).reindex(list(zip(tab.hari, tab.slot))).to_numpy()
    return pwv1.to_numpy() - nilai_acuan


def _persentil(pwv1, W, min_hari, awal_seri, reset, posisi):
    idx = pwv1.index; arr = pwv1.to_numpy(); out = np.full(len(arr), np.nan)
    for i in posisi:
        x = arr[i]
        if np.isnan(x): continue
        t = idx[i]
        j0 = max(t - W * HARI, awal_seri)
        if reset is not None and t >= reset:
            j0 = max(j0, reset)
        j1 = t - pd.Timedelta(hours=12)
        if j1 - j0 < min_hari * HARI: continue
        a, b = idx.searchsorted(j0), idx.searchsorted(j1)
        ref = arr[a:b]; ref = ref[~np.isnan(ref)]
        if len(ref) < min_hari * 24: continue
        out[i] = 100.0 * (ref < x).mean()
    return out


def hitung_fitur(v, jendela_hari=15, min_hari=3, awal_seri=None, reset=None, hanya_akhir=False):
    """v: Series PWV layak di grid 30 menit kontinu (indeks UTC, hasil `seri_layak`).
    awal_seri: awal seri data stasiun (default: awal v). reset: Timestamp UTC atau None.
    hanya_akhir=True menghitung persentil untuk slot terakhir saja (dipakai mesin per tick)."""
    if len(v) == 0:
        return pd.DataFrame(columns=['pwv_1jam', 'anomali', 'persentil', 'delta_3j', 'ada'])
    awal_seri = v.index[0] if awal_seri is None else awal_seri
    # Rata-rata 2 slot, ditulis eksplisit: rolling().mean() memakai jumlah berjalan sehingga hasilnya
    # berbeda ~1e-14 bergantung awal potongan, dan itu cukup membalik peringkat persentil pada nilai seri.
    sebelum = v.shift(1)
    pwv1 = ((v + sebelum) / 2).fillna(v).fillna(sebelum)
    d3 = pwv1 - pwv1.shift(6)
    anom = _anomali(pwv1, jendela_hari, min_hari, reset)
    posisi = [len(v) - 1] if hanya_akhir else range(len(v))
    pct = _persentil(pwv1, jendela_hari, min_hari, awal_seri, reset, posisi)
    f = pd.DataFrame({'pwv_1jam': pwv1.to_numpy(), 'anomali': anom, 'persentil': pct, 'delta_3j': d3.to_numpy()},
                     index=v.index)
    f['ada'] = f[['anomali', 'persentil', 'delta_3j']].notna().all(axis=1)
    return f
