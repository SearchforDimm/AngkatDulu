"""Jam mesin. JamReplay memutar waktu simulasi per 30 menit, bisa dipercepat, dijeda, dan dilompati (FR-02)."""
import threading
import time

import pandas as pd

from .waktu import SLOT, ke_utc


class JamReplay:
    def __init__(self, mulai, selesai, detik_per_tick=0.0, langkah=SLOT):
        self.mulai = ke_utc(mulai).floor('30min'); self.selesai = ke_utc(selesai)
        self.langkah = langkah; self.detik_per_tick = detik_per_tick
        self.sekarang = None
        self._jalan = threading.Event(); self._jalan.set()
        self._lompat = None

    def jeda(self): self._jalan.clear()
    def lanjut(self): self._jalan.set()
    def berjeda(self): return not self._jalan.is_set()
    def atur_kecepatan(self, detik_per_tick): self.detik_per_tick = max(0.0, float(detik_per_tick))
    def lompat(self, t): self._lompat = ke_utc(t).floor('30min')

    def maju(self):
        """Kembali waktu tick berikutnya, atau None bila sudah melewati `selesai`."""
        self._jalan.wait()
        if self._lompat is not None:
            self.sekarang, self._lompat = self._lompat, None
        else:
            self.sekarang = self.mulai if self.sekarang is None else self.sekarang + self.langkah
        if self.sekarang > self.selesai:
            return None
        if self.detik_per_tick > 0:
            time.sleep(self.detik_per_tick)
        return self.sekarang


class JamNyata:
    """Untuk mode live (nanti): tick pada setiap batas 30 menit jam dinding."""
    def maju(self):
        sekarang = pd.Timestamp.now(tz='UTC')
        berikut = sekarang.floor('30min') + SLOT
        time.sleep(max(0.0, (berikut - sekarang).total_seconds()))
        return berikut
