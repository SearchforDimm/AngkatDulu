"""SumberPWV: antarmuka `ambil(kode, sampai, sejak)` (PRD 10.1).

ReplaySource membaca database (view v_pwv_aktif) dan hanya mengembalikan slot yang SUDAH SELESAI
pada waktu `sampai` (waktu_utc + 30 menit <= sampai). Mesin tidak pernah melihat data masa depan.
LiveSource (nanti) memakai antarmuka yang sama.
"""
import pandas as pd

from .fitur import seri_layak
from .waktu import SLOT, ke_utc


class ReplaySource:
    def __init__(self, con):
        self.con = con; self._cache = {}

    def _muat(self, kode):
        if kode not in self._cache:
            df = pd.read_sql_query(
                'SELECT waktu_utc, pwv_mm, flag_kualitas FROM v_pwv_aktif WHERE kode_stasiun = ? ORDER BY waktu_utc',
                self.con, params=(kode,))
            df['waktu_utc'] = pd.to_datetime(df.waktu_utc, utc=True)
            self._cache[kode] = df
        return self._cache[kode]

    def daftar_stasiun(self):
        """Semua stasiun yang punya data PWV aktif."""
        return [r[0] for r in self.con.execute('SELECT DISTINCT kode_stasiun FROM v_pwv_aktif ORDER BY kode_stasiun')]

    def awal_seri(self, kode):
        df = self._muat(kode)
        return df.waktu_utc.min() if len(df) else None

    def ambil(self, kode, sampai, sejak=None):
        """Series PWV layak di grid 30 menit, slot [sejak, slot terakhir yang selesai <= sampai]."""
        sampai = ke_utc(sampai)
        df = self._muat(kode)
        akhir = sampai - SLOT                         # awal slot terakhir yang sudah selesai
        sejak = df.waktu_utc.min() if sejak is None else max(ke_utc(sejak), df.waktu_utc.min())
        if len(df) == 0 or akhir < sejak:
            return pd.Series(dtype=float)
        bagian = df[(df.waktu_utc >= sejak) & (df.waktu_utc <= akhir)]
        return seri_layak(bagian, mulai=sejak, akhir=akhir)
