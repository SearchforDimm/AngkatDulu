# Mesin peringatan, database, dan replay

## Database (`db/impor.py`)

```bash
python db/impor.py
```

Membangun `angkatdulu.db` (SQLite, tidak di-commit) dari `db/skema.sql`. Tabel: `stasiun, run_pengolahan, observasi_pwv, observasi_hujan, awal_hujan, aturan, aturan_stasiun, metrik_evaluasi, sesi_replay, status_stasiun, peringatan, pengguna, lokasi_pengguna, pesan, umpan_balik`. View: `v_pwv_aktif, v_pelanggan_stasiun, v_notifikasi_harian, v_rekam_jejak`.

## Mesin peringatan (`mesin/`)

Setiap **tick τ** (tiap 30 menit):

1. Untuk **semua** stasiun berdata (`stasiun_pantau`): ambil slot yang sudah selesai (`sumber.ambil`, tidak pernah data masa depan) → hitung fitur slot terakhir → nilai level (`PenilaiAturan`) → simpan `status_stasiun`.
2. Bila level berubah: buka/tutup baris `peringatan`. Bila stasiun punya pelanggan: rencanakan pesan sesuai kebijakan.
3. Penjadwal: ringkasan pagi 06.00 WIB; `TANYA_HUJAN` 90 menit setelah peringatan.
4. Pengirim: kirim pesan yang jatuh tempo (`PengirimLog` di replay, nanti bot Telegram).

**Level dan histeresis** (`mesin/aturan.py`):

- BERPOTENSI menyala saat persentil ≥ 80, padam 60 menit setelah syarat hilang.
- WASPADA sama, dengan persentil ≥ 65 (hanya tampil di status dan ringkasan pagi).
- TANPA_DATA bila fitur tidak lengkap ≥ 120 menit.

**Kebijakan pesan** (`mesin/kebijakan.py`):

| Aturan | Nilai |
|---|---|
| Jenis notifikasi berbunyi | BERPOTENSI dan AMAN_LAGI |
| Jam kirim | 06.00–18.00 WIB |
| Kuota | maksimal 2 notifikasi per chat per hari |
| AMAN_LAGI | hanya bila hari itu sudah ada BERPOTENSI, dan hanya sampai 15.00 WIB |
| Tanpa bunyi, di luar kuota | RINGKASAN_PAGI, TANYA_HUJAN, jawaban perintah |
| Alasan ditahan | `DI_LUAR_JAM`, `LEWAT_JAM_JEMUR`, `KUOTA_HARIAN` |

**Template pesan** (`mesin/template.py`): maksimal 3 kalimat, selalu menyebut stasiun dan jarak. Contoh BERPOTENSI: "Berpotensi hujan dalam 3 jam di sekitar stasiun CKRG (±3 km dari Anda). Siapkan terpal atau angkat jemuran. Bulan lalu di 4 stasiun, 15 dari 49 peringatan siang serupa diikuti hujan."

**Pengguna** (`mesin/pengguna.py`): lokasi pengguna dibulatkan 3 desimal (±100 m), stasiun = stasiun SEHAT terdekat. Pengguna uji replay memakai chat_id negatif dan titik jemur fiktif ±3 km dari stasiun.

## Replay dan uji

```bash
python replay.py --mulai "2026-10-25 05:00" --selesai "2026-10-25 20:00" --stasiun CKRG --cetak
python replay.py --mulai "2026-10-01" --selesai "2026-11-01" --ekspor log_replay
python pipeline/evaluasi/grafik_replay.py log_replay CKRG "2026-10-24 00:00" "2026-10-26 00:00" gambar.png
python -m pytest tests
```

- Mesin dipanaskan diam-diam 30 hari sebelum `--mulai` (status dan rekam jejak terisi tanpa pesan).
- `--detik-per-tick 1` memperlambat replay untuk demo.
- `periksa.py` memeriksa log: target **0 pelanggaran kebijakan pesan**.
- 17 uji otomatis: kausalitas fitur, kebijakan pesan, mesin = kalibrasi, hitungan evaluasi, ganti aturan.

## Konfigurasi

**`config/aturan.yaml`** (dibuat `kalibrasi.py`, dibaca mesin; aturan baru = baris baru di tabel `aturan`):

| Kunci | Nilai sekarang |
|---|---|
| `nama` / `versi` | `persentil-80` / `1.2.0` |
| `fitur.jendela_acuan_hari` / `min_hari_acuan` | 15 / 3 |
| `fitur.reset_acuan` | CJUR 2026-09-24 |
| `level2` | persentil ≥ 80, padam setelah 60 menit |
| `level1` | persentil ≥ 65 |
| `tanpa_data_setelah_menit` | 120 |
| `notifikasi` | 06:00–18:00 WIB, maks 2/hari (BERPOTENSI + AMAN_LAGI), tanya hujan +90 menit, aman lagi sampai 15:00 |

**`config/stasiun_live.yaml`**: RTCM ID, receiver, tipe antena + radome, tinggi antena untuk mode live (lihat [04_SUMBER_DATA_DAN_STASIUN.md](04_SUMBER_DATA_DAN_STASIUN.md)).

**`config/.env`** (dibuat sendiri dari `env_contoh.txt`, tidak pernah di-commit): `TELEGRAM_BOT_TOKEN`, nanti juga akun NTRIP.

---

Kembali ke [indeks](00_README.md).
