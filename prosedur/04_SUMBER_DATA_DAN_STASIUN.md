# Sumber data dan metadata stasiun

## Sumber data

| Data | Sumber | Format, resolusi | Latensi | Dipakai untuk |
|---|---|---|---|---|
| Pengamatan GNSS | SRGI (`srgi.big.go.id`), akun peserta | RINEX 2.11 (`.26o` + navigasi `.26n`), 30 detik | H+1, ±09.00 WIB | PPP → ZTD |
| Orbit & jam | CODE lewat CDDIS (`unduh_cddis.py`), akun Earthdata | SP3 5 menit, CLK 30 detik (`COD0MGXFIN`, cadangan `COD0OPSFIN`/`COD0OPSRAP`) | final ±2 minggu, rapid H+1 | PPP |
| Kalibrasi antena | IGS | `igs20.atx` | tetap | PPP |
| Tekanan & suhu | Copernicus CDS, ERA5 single levels | GRIB1, per jam, grid 0,25° (surface pressure, 2 m temperature) | ±5 hari | ZHD, Tm |
| Hujan | NASA GES DISC lewat Giovanni | CSV rata-rata area kotak kecil per stasiun, IMERG Late V07, 30 menit | ±14 jam (Late) | label kalibrasi & evaluasi, bukan input keputusan |
| Kesehatan & hardware stasiun | `nrtk.big.go.id` (akun peserta) | halaman web | live | metadata antena, status online |
| Stream real-time (rencana) | IGS-IP (`igs-ip.net`, `products.igs-ip.net`), akun BKG | RTCM 3 MSM7 + SSR | detik | mode live BAKO |

Periode data: **1 September – 1 November 2026** (DOY 244–306).

## Metadata stasiun

| Stasiun | Lokasi | Lintang, bujur | Tinggi ortometrik / elipsoid | RTCM ID | Receiver | Antena (radome), tinggi |
|---|---|---|---|---|---|---|
| CKRG | Karawang (stasiun demo) | −6,1112, 107,3280 | 8,0 / 27,6 m | 0406 | Trimble Alloy | TRM159900.00 SCIS, 0,000 m |
| BAKO | Cibinong, Bogor (juga stasiun IGS) | −6,4911, 106,8489 | 140,1 / 158,2 m | 0031 | Leica GR50 | LEIAR20 LEIM, 1,648 m |
| CLBG | Lembang, Bandung Barat | −6,8244, 107,6156 | 1.308,9 / 1.329,8 m | 0036 | Leica GR50 | LEIAT504GG LEIS, 0,008 m |
| CJUR | Cianjur | −6,8221, 107,1381 | 459,8 / 479,9 m | 0168 | Trimble Alloy | TRM159900.00 SCIS, 0,000 m (sejak 24 Sep) |

Catatan:

- **CJUR ganti perangkat**: DOY 244–245 Septentrio PolaRx5 + LEIAR25 LEIT; DOY 246–266 Trimble Alloy + LEIAR25 LEIT; mulai DOY 267 Trimble Alloy + TRM159900.00 SCIS. Koordinat dihitung terpisah (beda tinggi 11,5 cm), dan pembanding persentil dimulai ulang 24 Sep.
- **Radome di RINEX kosong** untuk CKRG dan BAKO, jadi olahan historis memakai `NONE`. Uji 10 hari: selisih ZTD SCIS−NONE (CKRG) 0,6 ± 0,3 mm, LEIM−NONE (BAKO) −0,3 ± 0,4 mm (±0,1 mm PWV). Data historis tidak perlu diolah ulang; mode live memakai radome yang benar.
- CLDO tidak dipakai (data SRGI berhenti awal September).

---

Kembali ke [indeks](00_README.md).
