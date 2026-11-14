"""Bantuan waktu. Semua waktu disimpan UTC (ISO 8601, akhiran Z) dan ditampilkan WIB (UTC+7)."""
import pandas as pd

WIB = pd.Timedelta(hours=7)
SLOT = pd.Timedelta(minutes=30)
BULAN = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des']


def ke_utc(x):
    """str / Timestamp -> Timestamp UTC. Waktu tanpa zona dianggap UTC."""
    t = pd.Timestamp(x)
    return t.tz_localize('UTC') if t.tzinfo is None else t.tz_convert('UTC')


def dari_wib(x):
    """Waktu WIB tanpa zona (mis. '2026-10-27 06:00') -> Timestamp UTC."""
    t = pd.Timestamp(x)
    if t.tzinfo is not None:
        return t.tz_convert('UTC')
    return (t - WIB).tz_localize('UTC')


def iso(t):
    return ke_utc(t).strftime('%Y-%m-%dT%H:%M:%SZ')


def wib(t):
    """Timestamp UTC -> Timestamp WIB tanpa zona."""
    return (ke_utc(t) + WIB).tz_localize(None)


def tanggal_wib(t):
    return wib(t).date()


def label_wib(t):
    w = wib(t)
    return f'{w.day} {BULAN[w.month - 1]} {w.hour:02d}.{w.minute:02d} WIB'
