"""Aturan peringatan (dibaca dari config/aturan.yaml) dan PenilaiAturan (fitur -> level, dengan histeresis).

PenilaiAturan dipakai mesin (per tick) dan kalibrasi (per slot), jadi perilaku keduanya identik.
Level: AMAN, WASPADA (Level 1), BERPOTENSI (Level 2), TANPA_DATA.
- BERPOTENSI menyala saat syarat Level 2 terpenuhi, padam setelah syarat hilang `padam_slot` slot berturut-turut.
- WASPADA sama, dengan syarat Level 1 (syarat Level 2 otomatis memenuhi Level 1).
- Slot tanpa fitur lengkap tidak mengubah status; bila berturut-turut >= `putus_slot` slot, status TANPA_DATA.
"""
import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import yaml

LEVEL = ('AMAN', 'WASPADA', 'BERPOTENSI', 'TANPA_DATA')


def _menit_ke_slot(menit):
    return max(1, int(round(menit / 30)))


def _jam(teks):
    j, m = str(teks).split(':')
    return int(j) + int(m) / 60


@dataclass
class Aturan:
    nama: str
    versi: str
    jenis: str                       # 'anomali' | 'persentil'
    l2_min: float | None             # ambang Level 2 (mm anomali atau persentil); None = tanpa syarat ini
    l2_delta: float | None = None    # syarat kenaikan 3 jam (mm); None = tidak dipakai
    l1_min: float | None = None      # ambang Level 1
    padam_slot: int = 2
    putus_slot: int = 4
    jendela_hari: int = 15
    min_hari: int = 3
    reset: dict = field(default_factory=dict)   # kode -> Timestamp UTC
    jam_mulai: float = 6.0
    jam_selesai: float = 18.0
    maks_per_hari: int = 2
    tanya_hujan_menit: int = 90
    aman_lagi_sampai: float = 15.0   # "aman lagi" = boleh jemur lagi; sesudah jam ini tidak dikirim
    asli: dict = field(default_factory=dict)

    @classmethod
    def dari_dict(cls, d):
        f = d.get('fitur', {}); l2 = d['level2']; l1 = d.get('level1', {}); n = d.get('notifikasi', {})
        return cls(
            nama=d['nama'], versi=str(d['versi']), jenis=l2['jenis'],
            l2_min=l2.get('min'), l2_delta=l2.get('delta3j_min_mm'), l1_min=l1.get('min'),
            padam_slot=_menit_ke_slot(l2.get('padam_setelah_menit', 60)),
            putus_slot=_menit_ke_slot(d.get('tanpa_data_setelah_menit', 120)),
            jendela_hari=int(f.get('jendela_acuan_hari', 15)), min_hari=int(f.get('min_hari_acuan', 3)),
            reset={k: pd.Timestamp(v, tz='UTC') if pd.Timestamp(v).tzinfo is None else pd.Timestamp(v).tz_convert('UTC')
                   for k, v in (f.get('reset_acuan') or {}).items()},
            jam_mulai=_jam(n.get('jam_mulai_wib', '06:00')), jam_selesai=_jam(n.get('jam_selesai_wib', '18:00')),
            maks_per_hari=int(n.get('maks_per_hari', 2)), tanya_hujan_menit=int(n.get('tanya_hujan_setelah_menit', 90)),
            aman_lagi_sampai=_jam(n.get('aman_lagi_sampai_wib', '15:00')),
            asli=d)

    @classmethod
    def dari_yaml(cls, path):
        return cls.dari_dict(yaml.safe_load(Path(path).read_text(encoding='utf-8')))

    def json(self):
        return json.dumps(self.asli, ensure_ascii=False, default=str)

    # ---- syarat
    def _x(self, f):
        return f.get(self.jenis)

    @staticmethod
    def _ok(x, batas):
        return batas is None or (x is not None and not (isinstance(x, float) and math.isnan(x)) and x >= batas)

    def syarat_l2(self, f):
        return self._ok(self._x(f), self.l2_min) and self._ok(f.get('delta_3j'), self.l2_delta)

    def syarat_l1(self, f):
        return self.syarat_l2(f) or (self.l1_min is not None and self._ok(self._x(f), self.l1_min))


class PenilaiAturan:
    def __init__(self, aturan):
        self.a = aturan
        self.on = False; self.mati = 0          # status Level 2
        self.w_on = False; self.w_mati = 0      # status Level 1
        self.putus = 0
        self.level = 'TANPA_DATA'

    def langkah(self, s2, s1, ada):
        """Satu slot. s2/s1: syarat Level 2/1 terpenuhi; ada: fitur lengkap. Kembali level baru."""
        if not ada:
            self.putus += 1
            if self.putus >= self.a.putus_slot:
                self.on = False; self.w_on = False; self.level = 'TANPA_DATA'
            return self.level
        self.putus = 0
        if s2:
            self.on = True; self.mati = 0
        elif self.on:
            self.mati += 1
            if self.mati >= self.a.padam_slot: self.on = False
        if s1 or s2:
            self.w_on = True; self.w_mati = 0
        elif self.w_on:
            self.w_mati += 1
            if self.w_mati >= self.a.padam_slot: self.w_on = False
        self.level = 'BERPOTENSI' if self.on else ('WASPADA' if self.w_on else 'AMAN')
        return self.level

    def nilai(self, f):
        """f: dict fitur (pwv_1jam, anomali, persentil, delta_3j, ada) atau None."""
        if not f or not f.get('ada'):
            return self.langkah(False, False, False)
        return self.langkah(self.a.syarat_l2(f), self.a.syarat_l1(f), True)
