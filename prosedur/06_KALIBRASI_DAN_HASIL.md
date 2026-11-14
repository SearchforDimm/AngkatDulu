# Kalibrasi, evaluasi, dan hasil

## Kalibrasi dan evaluasi (`kalibrasi.py` dan kawan-kawan)

```bash
python pipeline/evaluasi/kalibrasi.py
python pipeline/evaluasi/banding_gabungan.py FOLDER_GABUNG data/evaluasi/banding_gabungan.csv
python pipeline/evaluasi/selang_hss.py
```

`kalibrasi.py` dan `selang_hss.py` tanpa argumen mengumpulkan sendiri `data/pwv/` dan `data/hujan/`. `banding_gabungan.py` butuh satu folder (`FOLDER_GABUNG`) berisi `pwv_30menit_*.csv`, `hujan_30menit.csv`, dan `awal_hujan.csv` sekaligus: salin isi `data/pwv/` dan `data/hujan/` ke satu folder dulu.

- **Fitur kausal** (`mesin/fitur.py`, dipakai juga oleh mesin):
  - `pwv_1jam` = rata-rata 2 slot terakhir (t − 30 menit dan t), ditulis eksplisit agar hasil tidak bergantung pada awal potongan data.
  - `persentil` = peringkat `pwv_1jam` di antara nilai [t − 15 hari, t − 12 jam), minimal 3 hari data.
  - `anomali` = `pwv_1jam` dikurangi rata-rata jam yang sama 15 hari sebelumnya.
  - `delta_3j` = perubahan 3 jam.
  - Pembanding dimulai ulang pada `reset_acuan` (CJUR 24 Sep, ganti antena).
  - Hanya slot dengan flag `OK`, `METEO_ISI`, `ORBIT_RAPID` yang dipakai.
- **Keluarga aturan yang diuji**: ambang tetap, anomali, kenaikan 3 jam, persentil.
- **Skor**: HSS P-3J tiap slot siang (τ 06.00–17.59 WIB), POD, FAR, E-3J, notifikasi per hari (hanya hari yang punya PWV siang).
- **Skema uji**: (1) LOSO antarstasiun, (2) atur di September, uji di Oktober.
- **Aturan seri**: HSS dibulatkan 2 desimal, lalu E-3J terbanyak.
- **Hasil**: persentil 80 → `config/aturan.yaml`. Rincian di `data/evaluasi/`.

## Hasil utama

Data 4 stasiun, 1 Sep–1 Nov 2026, 66 awal hujan siang, uji silang antarstasiun:

| Aturan | HSS (selang 95%) | Awal hujan diperingatkan 0–3 jam | Notifikasi/hari |
|---|---|---|---|
| Pola harian 13–17 WIB | 0,18 (0,14–0,23) | 26/66 | 1,00 |
| Ambang tetap PWV ≥ 45 mm | 0,25 (0,17–0,34) | 18/66 | 0,41 |
| **PWV ≥ persentil 80** (aktif) | **0,32 (0,23–0,41)** | 16/66 | 0,44 |
| Persistensi | 0,40 (0,31–0,48) | 18/66 | 0,31 |
| Persentil 60 + persistensi | 0,42 (0,33–0,51) | 18/66 | 0,23 |

- Persentil 80: POD 54%, peringatan tepat 39% (per slot menyala), 28% notifikasi diikuti hujan.
- Selisih persentil − pola harian +0,14 (0,05–0,23), bermakna. Terhadap 45 mm (+0,07) dan persistensi (−0,08) belum bermakna.
- September → Oktober: HSS 0,23 (perlu kalibrasi per musim).
- Nilai ekonomi positif untuk rasio biaya/kerugian 11–39%.
- **Multi-GNSS**: GPS+GLONASS menaikkan satelit per epoch 8,7 → 14,0 dan menurunkan σ ZTD 5,0 → 4,3 mm; HSS sama di langit terbuka. Simulasi langit terhalang (elevasi < 30° dibuang): ZTD GPS saja gagal 26,8% epoch, GPS+GLONASS 0,3%.
- **Akurasi PWV**: literatur Ina-CORS 2,59 mm RMSD terhadap ERA5 (Wijaya dkk., 2024).

## Keterbatasan dan asumsi

- Data baru satu peralihan musim (2 bulan); CKRG hanya 3 awal hujan.
- Latensi RINEX H+1; ERA5 ±5 hari; IMERG Late ±14 jam, jadi mode replay belum real-time.
- Celah ERA5 28–31 Okt diisi (galat ±0,26 mm PWV).
- IMERG adalah estimasi satelit, bukan alat ukur hujan di lapangan; hujan konvektif kecil bisa terlewat.
- Radius layanan belum terukur; jarak antarstasiun ±60 km sedangkan sel hujan beberapa km, jadi pesan selalu menyebut jarak ke stasiun.
- Alarm palsu masih tinggi (FAR 0,61). PWV tinggi perlu ada agar hujan turun, tetapi belum cukup.
- RINEX 2.11 SRGI hanya memuat Galileo satu frekuensi dan tanpa BeiDou.
- PWV di dataran tinggi (CLBG) lebih tidak pasti karena tekanannya diekstrapolasi dari grid ERA5, sehingga aturan memakai persentil per stasiun, bukan ambang mutlak.

---

Kembali ke [indeks](00_README.md).
