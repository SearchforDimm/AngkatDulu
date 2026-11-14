# AngkatDulu: kode dan hasil olahan

Folder ini ditulis langsung oleh Claude ke laptop (`Documents\AngkatDulu\angkatdulu`). Buka di VS Code lewat **File → Open Folder…** dan pilih folder ini. Setiap file yang Claude tambah atau ubah langsung muncul di Explorer, jadi tidak perlu klik refresh.

Pengolahan yang berat (PPP RTKLIB untuk 60 hari × 4 stasiun) tetap jalan di workspace Claude, karena di sana `rnx2rtkp`, produk orbit/jam, dan RINEX sudah siap. Script dan hasilnya disalin ke sini supaya bisa dibaca, diperiksa, dan dicoba sendiri.

Alur kerja lengkap dan pembagian tugas: lihat [`WORKFLOW.md`](WORKFLOW.md).

## Status data (2 Nov 2026)

| Data | CKRG | BAKO | CLBG | CJUR |
|---|---|---|---|---|
| RINEX 1 Sep–1 Nov | ada (DOY 252–263 kosong) | ada (252–263, 269–270 kosong) | ada (259–264 kosong) | lengkap 244–306, tapi banyak hari berhenti 20.00 UTC |
| ZTD 30 detik (PPP-fixed G+R) | 50 hari, σ 3,8 mm, 14,8 satelit | 47 hari, σ 4,1 mm, 13,6 satelit | 56 hari, σ 4,0 mm, 13,9 satelit | 62 hari, σ 5,1 mm, 13,5 satelit |
| IMERG 30 menit | ada | ada | ada | ada |
| ERA5 tekanan + suhu | 1 Sep 00 – 28 Okt 09 UTC dan 1–3 Nov (28 Okt 10 – 31 Okt 23 UTC diisi) | sama | sama | sama |
| PWV 30 menit | 2.335 slot (1.931 OK) | 2.248 slot (1.860 OK) | 2.681 slot (2.295 OK) | 2.772 slot (2.349 OK) |
| Awal hujan siang dengan PWV (Sep / Okt) | 1 / 2 | 4 / 17 | 5 / 13 | 11 / 13 |

ERA5 28 Okt 10.00 – 31 Okt 23.00 UTC (86 jam) belum bisa diunduh. Jam itu diisi pola rata-rata per jam 14 hari sebelumnya, ditambah anomali yang ditarik lurus dari 6 jam sebelum ke 6 jam sesudah celah, lalu ditandai `ERA5_ISI` / `METEO_ISI`. Mesin tetap memakai slot itu. Uji pada 80 celah buatan 86 jam di Sep–Okt: galat PWV rata-rata 0,26 mm (95% jam < 0,55 mm); cara lama (pola saja) 0,35 mm. Kalau ERA5 28–31 Okt sudah bisa diunduh, jalankan ulang `pwv.py` dengan ketiga file GRIB.

Hari tanpa jendela 26 jam (data 22.00–24.00 UTC hari sebelumnya tidak ada, jadi 1 jam pertama ditandai `KONVERGENSI`): CKRG 244–250, 264, 280; BAKO 244, 265, 271; CLBG 244, 265; CJUR 244, 246–250, 255–267 (RINEX hari sebelumnya berhenti 19.59–20.59 UTC). Orbit/jam DOY 253, 255, 257, 259 sudah dilengkapi. CLDO tidak dipakai (data SRGI berhenti 4 Sep). Orbit DOY 298–305 masih *rapid* (`ORBIT_RAPID`).

## Struktur

```text
angkatdulu/
  pipeline/
    gnss/          siapkan_rinex.py  → sisip baris FCN GLONASS ke RINEX 2.11
                   jalankan_ppp.py   → PPP per hari, jendela 26 jam
                   ekstrak_ztd.py    → ztd_<st>.csv + qc_<st>.csv
                   statis.sh         → PPP-static satu hari (untuk koordinat stasiun baru)
                   konfig/           → konfigurasi rnx2rtkp (koordinat tetap CKRG, BAKO, CLBG, CJUR a/b)
    pwv/           pwv.py            → ZTD + ERA5 (boleh beberapa file GRIB) → pwv_30menit_<st>.csv (sesuai kontrak data)
                   grib1.py          → pembaca GRIB1 ERA5 tanpa pustaka tambahan
                   grafik_pwv.py     → grafik QC PWV + hujan IMERG
    evaluasi/      kalibrasi.py      → grid aturan + uji silang memakai kode mesin/ → config/aturan.yaml
                   banding_gabungan.py → bandingkan PWV dengan pola harian/persistensi dan gabungannya
                   grafik_banding.py → banding_aturan.png
                   grafik_replay.py  → grafik satu replay (PWV, ambang, status, notifikasi, hujan), Gambar 3 proposal
    hujan/         hujan.py          → IMERG → hujan_30menit.csv + awal_hujan.csv
                   cek_kejadian.py   → hitung awal hujan yang punya PWV per stasiun/bulan
    unduh/         unduh_cddis.py    → unduh orbit/jam CODE sekaligus (dijalankan di laptop)
    v0_okt/        pipeline lama 18–28 Okt (pwv.py, evaluasi.py, ringkasan_angka.py).
                   Masih memakai path workspace Claude, jadi untuk dibaca saja.
  data/ztd/        hasil ZTD 30 detik dan QC harian per stasiun
  data/pwv/        pwv_30menit_<st>.csv dan grafik_pwv_sep_okt.png
  data/hujan/      hujan_30menit.csv, awal_hujan.csv (CKRG, BAKO, CLBG, CJUR)
  data/evaluasi/   fitur.csv, grid_skor.csv, validasi.csv, banding_gabungan.csv, banding_aturan.png
  db/skema.sql     skema SQLite (15 tabel, 4 view), sesuai PRD bagian C
  db/impor.py      bangun angkatdulu.db dari data/ dan config/aturan.yaml (tahap 7)
  mesin/           mesin peringatan (tahap 8), satu kode untuk replay dan kalibrasi:
                   fitur.py (fitur kausal) · aturan.py (level + histeresis) · kebijakan.py (aturan pesan)
                   mesin.py (tick, peringatan, perencana pesan, ringkasan pagi, pengirim) · sumber.py (ReplaySource)
                   jam.py (JamReplay) · template.py (isi pesan) · pengguna.py · periksa.py · ekspor.py
  replay.py        putar ulang periode mana pun lewat mesin, cetak pesan, ekspor log CSV
  bot/             bot Telegram: telegram.py (klien Bot API) · layanan.py (pendaftaran, lokasi, "Tadi hujan?", pengirim)
  dasbor/          dashboard lokal (tahap 10): server.py (server HTTP 127.0.0.1, baca DB read-only) ·
                   index.html (satu halaman: status 4 stasiun, grafik PWV + ambang + hujan, log pesan, kendali replay)
  demo_bot.py      jalankan replay + bot Telegram + dashboard untuk demo dan video
  tests/           uji kausal, kebijakan pesan, mesin = kalibrasi, kinerja, ganti aturan
  config/          aturan.yaml (aturan aktif), env_contoh.txt (token bot nanti diisi di file .env, jangan di-commit)
```

Sudah ada: `bot/` (tahap 9, bot Telegram), `dasbor/` (tahap 10, dashboard), dan `demo_bot.py` yang menjalankan keduanya. File `config/aturan_v1.yaml` sudah digantikan `config/aturan.yaml` dan boleh dihapus.

## Ekstensi VS Code (opsional)

Tidak ada plugin yang wajib. Yang membantu:

- **Python** (Microsoft): membaca dan menjalankan file `.py`.
- **Rainbow CSV**: kolom CSV berwarna dan rapi.
- **Markdown Preview Mermaid Support**: diagram ERD di PRD tampil saat Preview (Ctrl+Shift+V).
- **SQLite Viewer**: membuka file `.db` nanti.

## Cara membaca hasil

- `data/ztd/qc_ckrg.csv`: satu baris per hari (status, ada jendela 26 jam atau tidak, produk orbit, jumlah epoch, rata-rata satelit, σ ZTD).
- `data/pwv/grafik_pwv_sep_okt.png`: lihat dulu ini. PWV per 30 menit dan hujan IMERG per stasiun.
- `data/pwv/pwv_30menit_ckrg.csv`: kolom sesuai tab *Kontrak Data* di spreadsheet. Mesin hanya memakai slot dengan `flag_kualitas` OK, METEO_ISI, atau ORBIT_RAPID.
- `data/ztd/ztd_ckrg.csv`: kolom `waktu_utc, ztd_m, sigma_m, flag, produk`. Waktu dalam UTC (WIB = UTC + 7).

## Menjalankan mesin di laptop

Butuh Python 3.11 atau lebih baru. Di terminal VS Code (**Terminal → New Terminal**), dari folder `angkatdulu`:

```bash
pip install -r requirements.txt
python db/impor.py                       # bangun angkatdulu.db (±1 detik)
python replay.py --mulai "2026-10-25 05:00" --selesai "2026-10-25 20:00" --stasiun CKRG --cetak
python -m pytest tests                   # ±4 menit
```

Contoh keluaran replay 25 Okt (CKRG, pengguna uji "Bu Sri"):

```text
(senyap) [RINGKASAN_PAGI] [REPLAY · 25 Okt 06.00 WIB] Selamat pagi, uap air 24 jam terakhir stabil. Status pagi ini waspada: ...
(notif)  [BERPOTENSI]     [REPLAY · 25 Okt 06.30 WIB] Berpotensi hujan dalam 3 jam di sekitar stasiun CKRG (±3 km dari Anda). ...
(senyap) [TANYA_HUJAN]    [REPLAY · 25 Okt 08.00 WIB] Tadi hujan di tempat Anda?
Pelanggaran kebijakan pesan: 0
```

Kalimat terakhir pesan BERPOTENSI berbunyi "Bulan lalu di 4 stasiun, 15 dari 49 peringatan siang serupa diikuti hujan." "Aman lagi" pukul 16.30 dicatat DITAHAN (`LEWAT_JAM_JEMUR`): sesudah 15.00 tidak ada waktu menjemur lagi. Mesin selalu memantau keempat stasiun supaya rekam jejak bisa digabung, tetapi pesan hanya dikirim ke pelanggan stasiun yang dipilih (`--stasiun`). Karena itu pemanasan 30 hari butuh ±50 detik di laptop Claude. IMERG mencatat awal hujan di CKRG pukul 07.30, satu jam setelah peringatan. Pilihan lain: `--ekspor log_replay` menyimpan status, peringatan, dan pesan ke CSV; `--detik-per-tick 1` memperlambat replay untuk demo.

## Menjalankan demo: bot Telegram dan dashboard (tahap 9–10)

Token bot disimpan di `config\.env` (`TELEGRAM_BOT_TOKEN=...`, contoh di `config\env_contoh.txt`). Bot butuh internet (tidak perlu IP publik); dashboard tidak.

```bash
python demo_bot.py --replay
```

1. Terminal menampilkan `Bot @nama_bot tersambung`, tautan `https://t.me/nama_bot`, dan `Dashboard: http://127.0.0.1:8000/`. Browser terbuka sendiri ke dashboard.
2. Di HP "Bu Sri": buka tautan bot, tekan **Start**, lalu tekan tombol **Kirim lokasi jemur**. Dalam mode demo, lokasi apa pun diganti titik jemur contoh ±3 km dari CKRG, supaya demo di Bogor tetap memakai data Karawang (`--lokasi-asli` untuk memakai lokasi sebenarnya).
3. Mesin dipanaskan (±1 menit). Dashboard menampilkan **Siap diputar** dan grafik 12 jam sebelumnya.
4. Tekan **Mulai replay** di dashboard. Replay 25 Okt 05.00–20.00 WIB berjalan 2 detik per 30 menit (±1 menit). HP menerima ringkasan pagi 06.00 (senyap), **"Berpotensi hujan" 06.30 (berbunyi)**, dan "Tadi hujan?" 08.00 dengan tombol jawaban. Dashboard menampilkan hal yang sama di panel **Pesan ke HP Bu Sri**, termasuk pesan yang ditahan beserta alasannya (16.30 lewat 15.00, 19.30 di luar jam).
5. Selama berjalan: **Jeda**/**Lanjutkan**, pilih **Kecepatan**, dan klik ubin stasiun untuk melihat grafiknya. Setelah selesai, **Putar ulang** membuat sesi baru (pemanasan lagi ±1 menit). Ctrl+C di terminal untuk keluar.

Isi dashboard: jam simulasi; status stasiun HP (warna + ikon + kalimat); grafik PWV 1 jam dengan garis batas berpotensi (persentil 80) dan waspada (persentil 65) yang dihitung persis seperti mesin, pita status, jam di luar jemur, tanda pesan, dan batang hujan IMERG (hanya slot yang sudah lewat); ubin 4 stasiun; log pesan dengan jawaban "Tadi hujan?"; rekam jejak 30 hari. Semua berkas ada di `dasbor/`, tanpa CDN dan tanpa internet.

Pilihan: `--tanpa-bot` (tanpa internet: pesan hanya tampil di dashboard), `--detik-per-tick 3` (lebih lambat untuk video), `--mulai`/`--selesai` (WIB), `--stasiun BAKO`, `--port 8001`, `--tanpa-browser`, `--langsung` (putaran pertama mulai tanpa tombol), `--tanpa-dasbor` (perilaku lama: replay langsung jalan, layani jawaban 2 menit). Tanpa `--replay`, bot hanya melayani pendaftaran. Perintah di HP: `/start`, `/status`, `/berhenti`.

PPP butuh `rnx2rtkp` (RTKLIB-EX 2.5.1) dan folder `prod/` berisi SP3, CLK, dan `igs20.atx` yang sudah diekstrak. Path di `jalankan_ppp.py` diatur untuk workspace Claude (Linux).

## Hasil kalibrasi aturan (tahap 5, final 9 Nov)

Lihat dulu `data/evaluasi/banding_aturan.png`. Rinciannya ada di `data/evaluasi/validasi.csv` dan `banding_gabungan.csv`; aturan aktif ada di `config/aturan.yaml`.

Sejak 5 Nov, kalibrasi memakai kode `mesin/` yang sama dengan mesin replay (diuji di `tests/test_mesin.py`: status dan waktu notifikasi identik selama 1 Sep–1 Nov). Kuota 2 notifikasi per hari kini juga menghitung AMAN_LAGI, sesuai proposal. Keluarga aturan dipilih dari uji silang: persentil HSS 0,32 dan anomali 0,31 (seri bila dibulatkan 2 desimal), tetapi persentil memperingatkan 16/66 awal hujan, anomali ≥ 12 mm hanya 9/66, jadi persentil dipakai. Di semua data, persentil 80 dan 85 juga seri (HSS 0,333 dan 0,333); dengan aturan seri yang sama, persentil 80 dipilih karena memperingatkan 19/66 awal hujan, persentil 85 hanya 14/66.

- Data: 4 stasiun, 1 Sep–1 Nov, **66 awal hujan siang** yang punya PWV di 3 jam sebelumnya (Sep 21, Okt 45).
- Uji utama: **uji silang per stasiun** (parameter dipilih di 3 stasiun, diuji di stasiun ke-4, bergantian). Uji kedua: atur di September, uji di Oktober.
- Skor P-3J dinilai tiap 30 menit pukul 06.00–18.00 WIB: apakah status BERPOTENSI tepat menandai hujan ≥ 1 mm/jam dalam 3 jam ke depan.

| Aturan (uji silang per stasiun) | HSS | POD | FAR | Awal hujan diperingatkan 0–3 jam | Notifikasi/hari |
|---|---|---|---|---|---|
| Pola harian (tiap 13–17 WIB) | 0,18 | 0,62 | 0,73 | 26/66 | 1,00 |
| Ambang tetap PWV ≥ 45 mm | 0,25 | 0,48 | 0,66 | 18/66 | 0,41 |
| **PWV ≥ persentil 80 stasiun** (aturan aktif) | **0,32** | 0,54 | 0,61 | 16/66 | 0,44 |
| PWV anomali ≥ 12 mm | 0,31 | 0,40 | 0,56 | 9/66 | 0,32 |
| Persistensi (hujan kemarin di 3 jam yang sama) | 0,40 | 0,52 | 0,51 | 18/66 | 0,31 |
| PWV ≥ persentil 60 **dan** persistensi | 0,42 | 0,43 | 0,40 | 18/66 | 0,23 |

Temuan:

1. Ambang mutlak tidak bisa dipindah antar stasiun. Di CLBG (1.309 m), PWV ≥ 45 mm hampir tidak pernah tercapai (0/18 awal hujan). Ambang per stasiun berbasis persentil 15 hari terakhir paling stabil.
2. Kenaikan PWV 3 jam (Δ3j) dan anomali per jam tidak menambah skor dibanding persentil saja. Syarat Level 2 "anomali + kenaikan" di PRD perlu diganti.
3. PWV saja mengalahkan pola harian, tetapi **kalah dari persistensi**. Gabungan PWV + persistensi paling baik dan mengirim notifikasi paling sedikit, tetapi selisihnya dengan persistensi saja kecil.
4. Hanya ±24% awal hujan (16/66) yang didahului peringatan baru 0–3 jam sebelumnya, dan 28% notifikasi diikuti hujan ≥ 1 mm/jam dalam 3 jam ("peringatan tepat" 39% di tabel dihitung per slot status menyala). Sisanya terjadi saat status sudah BERPOTENSI sejak lebih awal, atau tanpa sinyal PWV.
5. CKRG (stasiun demo) hanya punya 3 awal hujan, jadi skor per stasiunnya belum bisa dipercaya sendiri.
6. Rekam jejak CKRG saja terlalu sedikit kejadiannya ("1 dari 26" pada 25 Okt, karena September–Oktober di Karawang hampir kering). Sejak 9 Nov rekam jejak digabung dari 4 stasiun dan hanya menghitung peringatan yang mulai 06.00–18.00 (setara notifikasi): "15 dari 49" pada 25 Okt.

### Selang kepercayaan dan multi-GNSS

`python pipeline/evaluasi/selang_hss.py` (2.000 ulangan bootstrap per hari-stasiun, 196 hari-stasiun):

| Aturan | HSS | Selang 95% |
|---|---|---|
| Pola harian 13–17 WIB | 0,18 | 0,14–0,23 |
| Ambang tetap 45 mm | 0,25 | 0,17–0,34 |
| **PWV ≥ persentil 80** | **0,32** | 0,23–0,41 |
| Persistensi | 0,40 | 0,31–0,48 |
| PWV ≥ persentil 60 dan persistensi | 0,42 | 0,33–0,51 |

Selisih persentil 80 dengan pola harian +0,14 (0,05–0,23) bermakna; dengan ambang 45 mm (+0,07) dan persistensi (−0,08) belum. Gabungan vs persistensi +0,02 (−0,03–0,07): setara.

GPS saja vs GPS+GLONASS (215 hari-stasiun, PPP dan kalibrasi yang sama; `data/evaluasi/banding_gnss.csv`): satelit per epoch 8,7 → 14,0, σ ZTD 5,0 → 4,3 mm, selisih PWV RMS 1,2–2,0 mm, HSS sama (0,32). RINEX 2.11 SRGI memuat Galileo hanya pada E1 (satu frekuensi) dan tidak memuat BeiDou, jadi PPP dua frekuensi hanya bisa GPS + GLONASS.

Simulasi langit terhalang (pengamatan di bawah elevasi 30° dibuang secara buatan, bukan kondisi lapangan; relevan untuk receiver murah di balai desa; 18–27 Okt, 40 hari-stasiun; konfig `*_g30.conf` / `*_gr30.conf`, `pipeline/evaluasi/banding_gnss.py`): ZTD GPS saja hilang atau meleset > 10 cm pada 26,8% epoch, GPS+GLONASS 0,3%. Saat solusi ada, ketelitiannya mirip (median selisih ±19–20 mm). Jadi manfaat GLONASS adalah keandalan, bukan skor di langit terbuka.

## Catatan metode PWV

- Tekanan stasiun: tinggi tiap titik grid ERA5 ditaksir dari tekanan rata-ratanya terhadap baris laut (lintang −6,0). Tiap jam, tekanan grid diturunkan ke muka laut, diinterpolasi ke stasiun, lalu dinaikkan ke tinggi stasiun (CKRG 8,0 m, BAKO 140,1 m di atas geoid EGM96).
- ZHD Saastamoinen, Tm Bevis (70,2 + 0,72 Ts), faktor Π rata-rata 0,164.
- Cek silang dengan pipeline lama 18–28 Okt (CKRG, 516 slot): selisih rata-rata +0,30 mm, RMSE 0,41 mm, r 1,000. Selisihnya terutama dari tinggi stasiun 5 → 8 m dan cara interpolasi tekanan. Angka proposal (S-45, P-3J, dst.) perlu dihitung ulang dengan PWV baru.
- PWV CKRG dan BAKO (±55 km): r 0,886, rata-rata CKRG 0,67 mm lebih rendah.
- CLBG berada di 1.309 m (elipsoid 1.329,8 m, antena LEIAT504GG radome LEIS). Median PWV 24 mm, sekitar 18 mm lebih rendah dari BAKO, sesuai dengan uap air yang menipis ke atas (r CLBG–BAKO 0,929). Beberapa pagi di awal September turun ke 4–5 mm. Nilai mutlak di dataran tinggi lebih tidak pasti karena tekanannya diekstrapolasi dari grid ERA5 (titik grid terdekat 560–1.090 m), jadi aturan untuk CLBG harus memakai anomali atau persentil per stasiun, bukan ambang mutlak 45 mm.
- CJUR (Cianjur, 459,8 m) **berganti perangkat**: DOY 244–245 Septentrio PolaRx5 + LEIAR25 LEIT, DOY 246–266 Trimble Alloy + LEIAR25 LEIT, mulai DOY 267 (24 Sep) Trimble Alloy + TRM159900.00 SCIS. Koordinat tetap dihitung terpisah untuk dua periode antena (`fix_cjur_a.conf`, `fix_cjur_b.conf`); tinggi elipsoidnya berbeda 11,5 cm. Dibanding rata-rata BAKO dan CLBG, PWV CJUR sesudah 24 Sep sekitar 3 mm lebih rendah, jadi mungkin ada loncatan kecil akibat ganti antena. Rata-rata pembanding (*baseline*) anomali untuk CJUR dimulai ulang pada 24 Sep.
- PWV CJUR berada di antara BAKO dan CLBG, sesuai ketinggiannya (r terhadap BAKO 0,926, terhadap CLBG 0,921).

## Catatan perubahan

- **9 Nov 2026, larut (2)**: Perbaikan hitungan notifikasi per hari di `kalibrasi.nilai`: pembilang kini hanya notifikasi di hari yang dinilai (ada PWV siang), sama dengan penyebutnya. Sebelumnya pola harian tampak 1,14 per hari (seharusnya 1,00). HSS tidak berubah. Tes baru `test_evaluasi.py`; 17 tes.
- **9 Nov 2026, larut**: Review proposal. (1) "Aman lagi" hanya sampai 15.00 (`aman_lagi_sampai_wib`, alasan DITAHAN `LEWAT_JAM_JEMUR`), aturan 1.2.0, tes baru di `test_kebijakan.py`. (2) Rekam jejak hanya peringatan siang. (3) `selang_hss.py`: selang 95% HSS dengan bootstrap per hari-stasiun → `selang_hss.csv`. (4) GPS saja vs GPS+GLONASS untuk 215 hari-stasiun (`konfig/*_g.conf`, navsys=1) → `banding_gnss.csv`. 16 tes lulus.
- **9 Nov 2026, malam**: Rekam jejak di pesan BERPOTENSI digabung dari semua stasiun yang dipantau. Mesin kini selalu menghitung status semua stasiun berdata (`stasiun_pantau`); pesan tetap hanya ke pelanggan stasiun terpilih. 15 tes lulus.
- **9 Nov 2026**: ERA5 1–3 Nov masuk; celah 28–31 Okt diisi pola + anomali antar-tepi (`pwv.py` kini menerima beberapa GRIB). PWV 4 stasiun dan kalibrasi diulang: aturan tetap persentil 80, versi 1.1.0 (bukan draft lagi). Perbaikan `mesin/fitur.py`: rata-rata 1 jam ditulis eksplisit, karena `rolling().mean()` memberi selisih ~1e-14 yang membalik peringkat persentil pada nilai seri (mesin ≠ kalibrasi di 1 slot BAKO). Tes baru `test_fitur_tidak_bergantung_awal_potongan`; 15 tes lulus.
- **5 Nov 2026**: Tahap 7–8: `db/impor.py`, paket `mesin/`, `replay.py`, `tests/` (14 tes lulus). Kalibrasi dipindah ke kode mesin; aturan aktif `config/aturan.yaml` (persentil 80, draft).
- **2 Nov 2026, malam**: Orbit/jam DOY 253–259 dilengkapi; CLBG 56 hari, CJUR 62 hari. IMERG CJUR masuk. Kalibrasi putaran 1: `aturan_v1.yaml` (persentil 80), hasil uji di `data/evaluasi/`.
- **2 Nov 2026, malam**: CJUR diolah (58 hari, 2 periode antena). IMERG CJUR belum ada.
- **2 Nov 2026, malam**: CLBG diolah (koordinat PPP-static, ZTD 51 hari, PWV). Tabel hujan dan awal hujan untuk 3 stasiun.
- **2 Nov 2026, malam**: RINEX CLDO di SRGI berhenti di DOY 247. Pengganti yang diusulkan: CJUR (utama), CUMI (cadangan).
- **2 Nov 2026, sore**: `WORKFLOW.md` dan `docs/workflow.png` ditambahkan.
- **2 Nov 2026, sore**: PWV 30 menit CKRG dan BAKO dari ERA5 1 Sep–28 Okt, plus grafik QC.
- **2 Nov 2026**: folder dibuat. ZTD CKRG (50 hari) dan BAKO (47 hari) termasuk DOY 250 dan 278 yang baru dilengkapi.
