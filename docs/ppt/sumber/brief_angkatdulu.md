# Brief: deck pitch AngkatDulu (untuk skill ppt-master)

## Tugas

Buat deck presentasi PowerPoint **16:9, 11 slide, bahasa Indonesia** untuk pitch tim AngkatDulu di Demo Day BIG Bhumireka 2026, memakai skill ppt-master.

1. Baca `SKILL.md` ppt-master lebih dulu dan ikuti alurnya. Jangan pakai quick mode.
2. Semua bahan ada di folder `sumber/` (daftar di bagian "Bahan"). Kalau alur ppt-master memakai `projects/<nama>/sources/`, salin isi `sumber/` ke sana.
3. Usulkan design spec (template, format, jumlah halaman, palet, huruf) dan tunggu persetujuan saya sebelum membuat halaman.
4. Keluaran: PPTX yang bisa diedit, PDF cadangan, dan **catatan pembicara (speaker notes) berbahasa Indonesia** di setiap slide, diambil dari naskah di bawah.
5. Pakai hanya angka dan fakta dari brief ini. Kalau butuh angka lain, tanyakan dulu; jangan mengarang.

## Konteks lomba

- **Acara:** BIG Bhumireka 2026 (Badan Informasi Geospasial). Demo Day Kamis 19 Nov 2026 di BIG Cibinong, Bogor. AngkatDulu tampil urutan ke-5, sesi 10.00–10.30.
- **Format:** presentasi **5 menit + video 1 menit**, diputar dari laptop panitia. Maksimal 3 orang bicara; semua anggota naik panggung.
- **Wajib dibahas:** latar belakang pemilihan isu, metodologi, hasil, penyelesaian masalah.
- **Penilaian (5 × 20%):** kesesuaian tema, prototipe fungsional (dibuktikan lewat video 1 menit), inovasi futuristik (5–10 tahun ke depan), kesiapan presentasi, kesiapan demonstrasi.
- **Juri:** ahli geodesi dan GNSS dari BIG. Istilah dan angka harus tepat; klaim berlebihan akan merugikan.
- **Pengiriman:** Senin 16 Nov 2026 pukul 23.59 WIB ke kerjasama@big.go.id, subjek "BIG Bhumireka 2026 – AngkatDulu": PPT (berisi video), MP4 terpisah, dan PDF.

## Produk dalam satu paragraf

AngkatDulu memakai stasiun GNSS Ina-CORS milik BIG sebagai sensor uap air. Sinyal satelit melambat saat menembus uap air; keterlambatan itu dihitung lewat PPP (GPS + GLONASS), diubah menjadi PWV (precipitable water vapor, mm), dibandingkan dengan persentil 15 hari terakhir stasiun itu, lalu dikirim sebagai pesan Telegram "berpotensi hujan" kepada petani yang sedang menjemur gabah. Pesannya sopan: hanya 06.00–18.00 WIB, paling banyak 2 notifikasi per hari, dan "aman menjemur lagi" hanya sampai 15.00. Setiap pesan menyebut stasiun, jarak, dan rekam jejak terbuka. Persona demo: **Bu Sri** (ilustratif), petani gabah di Jayakerta, Karawang, dengan stasiun terdekat CKRG (±3 km).

- **Tagline:** "Angkat dulu, jemur lagi."
- **Kalimat penutup:** "Infrastrukturnya sudah ada di 474 titik. AngkatDulu membuatnya bicara dalam bahasa yang dimengerti Bu Sri: angkat dulu, atau jemur lagi."

## Kerangka 11 slide, waktu, dan pembicara

Pembicara 1 = isu dan insight (slide 1–3). Pembicara 2 = metodologi dan hasil (slide 4–7). Pembicara 3 = penyelesaian masalah dan masa depan (slide 8–11). Total 5 menit, ditambah video 1 menit di slide 5.

| # | Judul | Isi | Visual | Waktu |
|---|---|---|---|---|
| 1 | AngkatDulu | nama tim [ISI], tagline, logo, "BIG Bhumireka 2026 · Demo Day 19 Nov 2026" | logo (sumber/logo.svg) | 0:00–0:05 |
| 2 | Lima menit untuk menyelamatkan gabah | cerita Bu Sri; tiga angka besar: susut penjemuran 3,59%, ±Rp16,8 triliun per tahun (batas atas), musim hujan 2026/2027 mundur di 61,08% wilayah | tiga angka besar + ilustrasi lantai jemur (opsional dari video) | 0:05–0:40 |
| 3 | Sensor yang sudah ada | 474 stasiun Ina-CORS merekam sinyal satelit tiap detik; sinyal melambat sebanding uap air; radar BMKG baru 44 unit; GNSS melihat uap air sebelum awan hujan terbentuk; belum ada yang mengubahnya jadi keputusan "angkat atau tunggu" | diagram sederhana: satelit → lapisan uap air → antena | 0:40–1:15 |
| 4 | Cara kerja | rantai: RINEX Ina-CORS → PPP GPS+GLONASS (RTKLIB-EX) → ZTD → PWV (ERA5, Saastamoinen, Bevis) → persentil 15 hari per stasiun → status AMAN / WASPADA / BERPOTENSI → kebijakan pesan → Telegram dan dashboard; rumus PWV kecil | diagram alur digambar ulang (lihat "Arsitektur") + tangkapan dashboard | 1:15–2:15 |
| 5 | Video 1 menit | video demo diputar penuh | slide penuh untuk video; sisipkan MP4 (lihat "Bahan") | (1 menit) |
| 6 | Hasil uji | HSS 5 aturan (grafik batang), persentil 80 = 0,32 vs pola harian 0,18 (selisih +0,14, bermakna), 0,44 notifikasi/hari; jujur: persistensi 0,40, gabungan 0,42 jadi versi 2; contoh replay 24–25 Okt | grafik HSS native + gambar3_replay | 2:15–2:55 |
| 7 | Multi-GNSS | GPS+GLONASS: satelit per epoch 8,7 → 14,0; σ ZTD 5,0 → 4,3 mm; langit terhalang (elevasi < 30° dibuang): ZTD gagal 26,8% (GPS saja) vs 0,3% (GPS+GLONASS) | tiga angka perbandingan sebelum → sesudah | 2:55–3:15 |
| 8 | Masalah yang kami pecahkan | 3–4 pasangan masalah → solusi (lihat "Penyelesaian masalah") | pasangan masalah → solusi; jangan kartu seragam berikon | 3:15–3:55 |
| 9 | Tech stack dan biaya | lapisan teknologi; biaya komponen prototipe Rp0; operasional pilot ±Rp200 ribu/bulan | tabel ringkas per lapisan | 3:55–4:15 |
| 10 | 5–10 tahun lagi | matriks kelayakan–dampak + peta jalan 4 tahap | matriks 2×2 + linimasa | 4:15–4:50 |
| 11 | Terima kasih | kontak [ISI], QR bot Telegram [ISI: username bot], tagline, kalimat penutup | logo + QR | 4:50–5:00 |

## Naskah per bagian (masukkan ke speaker notes, boleh dirapikan)

- **Isu (slide 2):** Bu Sri menghamparkan gabah hasil kerja empat bulan di lantai jemur. Begitu langit gelap, ia hanya punya beberapa menit untuk menyapu dan menutupnya, sering sendirian. Susut padi saat penjemuran 3,59%; skalanya hingga ±Rp16,8 triliun per tahun. Musim hujan 2026/2027 mundur di 61% wilayah, jadi hujan turun di sela hari-hari cerah, justru saat petani berani menjemur.
- **Insight (slide 3):** 474 stasiun Ina-CORS sudah "mencium" uap air setiap detik. Yang belum ada: mengubahnya menjadi keputusan angkat atau tunggu.
- **Metodologi (slide 4):** RINEX → PPP GPS+GLONASS → ZTD → PWV → persentil 15 hari per stasiun → pesan Telegram dengan aturan sopan (06–18, maks 2/hari, aman lagi s.d. 15.00).
- **Hasil (slide 6–7):** HSS 0,32 vs 0,18 (bermakna), 0,44 notifikasi/hari. Jujur: "kemarin hujan" 0,40; gabungan 0,42 menjadi versi 2. Multi-GNSS: 26,8% vs 0,3% saat langit terhalang.
- **Penyelesaian masalah (slide 8–9):** ambang mutlak gagal di Lembang → persentil per stasiun; tanpa koreksi orbit PWV meleset 9–14 mm → koreksi SSR real-time; stream BIG terganggu → BAKO lewat IGS; biaya komponen Rp0.
- **Masa depan (slide 10–11):** receiver murah di balai desa, asimilasi PWV ke model cuaca, indeks hujan untuk asuransi; kuadran dampak tinggi dan layak. Tutup dengan kalimat penutup.

## Angka dan fakta (sudah diperiksa; pakai persis)

**Masalah**

| Fakta | Angka | Sumber |
|---|---|---|
| Susut padi saat penjemuran | 3,59% | Ditjen PPHP, Kementerian Pertanian (2008) |
| Produksi padi 2025 | 71,95 juta ton GKP | BPS (2026) |
| Harga Pembelian Pemerintah gabah | Rp6.500/kg | Bapanas (2025) |
| Nilai susut penjemuran (batas atas) | ±Rp16,8 triliun per tahun | hitungan dari tiga baris di atas |
| Per petani berlahan 0,5 ha | ±Rp742 ribu per panen | hitungan yang sama |
| Awal musim hujan 2026/2027 mundur | 61,08% daratan Indonesia | BMKG (2026) |
| Rumah tangga usaha pertanian | 28,4 juta (16,89 juta petani gurem) | Sensus Pertanian 2023, BPS |
| Penetrasi internet perdesaan | 76,96% | APJII (2025) |
| Radar cuaca BMKG | 44 unit (Maret 2026) | InfoPublik (2026) |
| Stasiun Ina-CORS milik BIG | 474 | BIG |

Rp16,8 triliun hanya menunjukkan **skala masalah** (tidak semua susut karena hujan), bukan klaim manfaat AngkatDulu. Tulis "batas atas" atau "skala".

**Data dan pengujian**

- 4 stasiun: CKRG (Karawang), BAKO (Cibinong, di kompleks BIG, juga stasiun IGS), CLBG (Lembang), CJUR (Cianjur).
- Periode 1 Sep–1 Nov 2026, 66 awal hujan siang, uji silang antarstasiun (aturan dipilih di 3 stasiun, diuji di stasiun ke-4 bergantian). Hujan pembanding: GPM IMERG Late V07 (hanya untuk kalibrasi dan evaluasi, bukan input keputusan).
- Akurasi PWV menurut literatur Ina-CORS: 2,59 mm RMSD terhadap ERA5 (Wijaya dkk., 2024). Korelasi PWV CKRG–BAKO 0,886.
- 32 uji otomatis (pytest), termasuk uji bahwa mesin tidak pernah melihat data masa depan.

**Hasil HSS** (hujan ≥ 1 mm/jam dalam 3 jam ke depan; buat grafik batang native yang bisa diedit)

| Aturan | HSS (selang 95%) | Awal hujan diperingatkan 0–3 jam | Notifikasi/hari | Pakai PWV? |
|---|---|---|---|---|
| Pola harian 13–17 WIB | 0,18 (0,14–0,23) | 26/66 | 1,00 | tidak |
| Ambang tetap PWV ≥ 45 mm | 0,25 (0,17–0,34) | 18/66 | 0,41 | ya |
| **PWV ≥ persentil 80 (aktif)** | **0,32 (0,23–0,41)** | 16/66 | 0,44 | ya |
| Persistensi (hujan kemarin, jam sama) | 0,40 (0,31–0,48) | 18/66 | 0,31 | tidak |
| Persentil 60 + persistensi (versi 2) | 0,42 (0,33–0,51) | 18/66 | 0,23 | ya |

- Persentil 80 − pola harian = +0,14 (selang 95% 0,05–0,23), bermakna. Terhadap 45 mm (+0,07) dan persistensi (−0,08) belum bermakna.
- Persentil 80: POD 54%; 39% jam status menyala diikuti hujan; 28% notifikasi diikuti hujan dalam 3 jam; FAR 0,61.
- Nilai ekonomi positif untuk rasio biaya/kerugian 11–39%.
- HSS 0 = sama dengan menebak acak.

**Multi-GNSS:** GPS+GLONASS menaikkan satelit per epoch 8,7 → 14,0 dan menurunkan σ ZTD 5,0 → 4,3 mm. Simulasi langit terhalang (elevasi < 30° dibuang): ZTD GPS saja gagal 26,8% epoch, GPS+GLONASS 0,3%.

**Contoh replay 25 Okt 2026, stasiun CKRG (sama dengan isi video):** 06.00 ringkasan pagi (tanpa bunyi, status waspada) → 06.30 PWV 1 jam 44,4 mm melewati batas berpotensi 43,9 mm, notifikasi berbunyi → 07.30 hujan mulai (IMERG) → 08.00 bot bertanya "Tadi hujan?" dan Bu Sri menjawab "Hujan". Isi pesan 06.30: "Berpotensi hujan dalam 3 jam di sekitar stasiun CKRG (±3 km dari Anda). Siapkan terpal atau angkat jemuran. Bulan lalu di 4 stasiun, 15 dari 49 peringatan siang serupa diikuti hujan."

**Penyelesaian masalah (slide 8)**

| Masalah | Solusi |
|---|---|
| Ambang PWV mutlak gagal di dataran tinggi (Lembang jauh lebih kering) | ambang per stasiun: persentil 80 dari 15 hari terakhir |
| Tanpa koreksi orbit/jam, PWV real-time meleset 9–14 mm | koreksi SSR real-time (CNES `SSRA00CNE0`, sudah diterima 13 Nov) |
| Stream khusus BIG sedang terganggu | stream BAKO lewat jaringan IGS untuk mode live (tahap uji) |
| Data ERA5 kosong 86 jam (28–31 Okt) | diisi pola harian + interpolasi anomali; galat rata-rata 0,26 mm PWV |

**Tech stack (slide 9)**

| Lapisan | Teknologi |
|---|---|
| Pengamatan | Ina-CORS BIG, RINEX 2.11 dari SRGI (30 detik) |
| Orbit dan jam | CODE MGEX (NASA CDDIS); SSR CNES untuk live |
| Pengolahan GNSS | RTKLIB-EX 2.5.1, PPP-fixed GPS+GLONASS |
| Meteorologi | ERA5 (tekanan, suhu) |
| Hujan pembanding | GPM IMERG Late V07 |
| Mesin dan data | Python 3.11, pandas, SQLite |
| Pesan | Telegram Bot API |
| Dashboard | halaman web lokal, jalan tanpa internet |
| Pengujian | pytest, 32 uji |

Biaya: komponen prototipe **Rp0** (data dan perangkat lunak terbuka); operasional pilot **±Rp200 ribu per bulan**.

**Masa depan (slide 10)**

- Matriks kelayakan × dampak: radar cuaca baru = dampak tinggi tetapi mahal (kelayakan rendah); AngkatDulu = dampak tinggi dan layak, karena memakai infrastruktur yang sudah ada. Jangan menambah titik lain tanpa persetujuan saya.
- Peta jalan 4 tahap: tahun 1 pilot 3–5 stasiun; tahun 2–3 feed ZWD SRGI, radar BMKG, receiver GNSS murah di balai desa; tahun 4–6 peringatan banjir kilat untuk BPBD dan WhatsApp resmi; tahun 7–10 densifikasi nasional, asimilasi PWV ke model cuaca, indeks hujan untuk asuransi pertanian.

## Rumus (slide 4, kecil, sebagai persamaan yang bisa diedit)

- ZHD = 0,0022768 · P / (1 − 0,00266 · cos 2φ − 0,00028 · h) (Saastamoinen)
- ZWD = ZTD − ZHD
- Tm = 70,2 + 0,72 · Ts (Bevis)
- PWV = Π · ZWD, dengan Π rata-rata 0,164

## Arsitektur (gambar ulang sebagai diagram native)

```
RINEX Ina-CORS (SRGI, 30 detik) ─┐
Orbit & jam presisi (CODE) ──────┴→ PPP-fixed GPS+GLONASS (RTKLIB-EX) → ZTD 30 detik ─┐
Tekanan & suhu (ERA5) → ZHD, Tm ──────────────────────────────────────────────────────┴→ PWV 30 menit
PWV 30 menit → fitur kausal (persentil 15 hari) → status stasiun (AMAN / WASPADA / BERPOTENSI)
            → kebijakan pesan (06–18 WIB, maks 2/hari) → pesan Telegram ke penjemur + dashboard
Hujan IMERG ┄┄ hanya untuk kalibrasi & evaluasi ┄┄→ kalibrasi aturan ┄┄ aturan.yaml ┄┄→ status stasiun
```

Dua mode: **replay** (berjalan; data historis diputar seolah real-time) dan **live** (tahap uji: stream BAKO lewat IGS + koreksi SSR).

## Identitas visual (samakan dengan dashboard dan video)

- **Palet:** latar abu semen `#E4E6E0`, panel putih `#FFFFFF`, tinta `#17201A`, tinta sekunder `#47504A`, biru terpal `#1E6FD1` (aksen utama, seri PWV), emas gabah `#C99A2E`.
- **Warna status:** AMAN `#1A7F37`, WASPADA `#F5B223`, BERPOTENSI `#C8322F`, TANPA DATA `#69716A`. Status tidak boleh dibedakan dengan warna saja; selalu ada teks (dan ikon bila perlu).
- **Huruf:** judul Bahnschrift (berat semibold/bold), teks Segoe UI. Keduanya ada di Windows 10+. Kalau ppt-master mengusulkan huruf lain, pastikan tersedia di laptop panitia atau ditanam di file.
- **Logo:** `sumber/logo.svg` (atap biru terpal + garis emas gabah) diikuti tulisan "AngkatDulu" dalam Bahnschrift bold. Jangan menggambar ulang logo dengan gaya lain.
- **Gaya:** terang (proyektor di ruang terang), tenang, jujur, berbasis data. Satu gagasan per slide; angka penting besar. Teks isi minimal 24 pt, judul minimal 40 pt. Sumber ditulis kecil di kaki slide.
- **Hindari:** gradien ungu, glassmorphism, emoji, bayangan tebal, kartu metrik seragam tanpa makna, tulisan kecil di atas judul (eyebrow), ikon generik berlebihan.

## Aturan kejujuran (penting untuk juri BIG)

- Demo dan video memakai **mode replay** data 25 Oktober 2026. Jangan menyiratkan data live. Tulis "replay" di mana pun dashboard atau pesan ditampilkan.
- Peringatan masuk **satu jam** sebelum hujan (06.30 → 07.30). Pesannya berbunyi "berpotensi hujan dalam 3 jam", jadi **jangan** menulis "peringatan 3 jam sebelum hujan".
- Jawaban "Tadi hujan?" **dicatat** sebagai data uji lapangan; kalibrasi ulang ambang dari jawaban itu adalah **rencana pilot**, bukan fitur yang sudah berjalan.
- Bu Sri adalah persona ilustratif.
- Keterbatasan yang boleh disebut terbuka: data baru 2 bulan (satu peralihan musim, HSS September → Oktober 0,23); alarm palsu masih tinggi (FAR 0,61); radius layanan belum terukur (jarak antarstasiun ±60 km).
- Jangan membuat gambar AI untuk grafik, peta, tangkapan layar dashboard, atau tampilan Telegram. Pakai berkas asli dari `sumber/`. Ilustrasi AI hanya boleh untuk suasana (lantai jemur, Bu Sri) dan sebaiknya memakai gambar dari video tim bila disediakan.

## Bahan di folder `sumber/`

| Berkas | Isi | Slide |
|---|---|---|
| `brief_angkatdulu.md` | brief ini | – |
| `logo.svg` | simbol logo vektor | 1, 11 |
| `logo_tagline_transparan.png` | panel logo + tagline, latar transparan, 1920×1080 | 1 atau 11 |
| `kartu_akhir_penuh.png` | logo + tagline di latar semen, 1920×1080 | 11 (cadangan) |
| `gambar3_replay_ckrg_24-25okt.png` | grafik replay CKRG 24–25 Okt: PWV 1 jam, ambang persentil 80, notifikasi 06.30, "aman lagi" ditahan, hujan IMERG (awal hujan 07.30) | 6 |
| `banding_aturan.png` | grafik HSS 5 aturan (acuan; lebih baik digambar ulang sebagai grafik native dari tabel di atas) | 6 |
| `dasbor_0630_berpotensi.png` | tangkapan dashboard asli 06.30: status berubah merah "Berpotensi hujan dalam 3 jam", grafik PWV melewati batas | 4 |
| `dasbor_0800_hujan_tercatat.png` | dashboard asli 08.00: batang hujan IMERG dan "hujan mulai 07.30" | 6 (opsional) |
| `dasbor_4stasiun_bako.png` | dashboard asli dengan grafik BAKO terpilih (4 ubin stasiun terlihat) | 9 (opsional) |
| [disediakan tim] video 1 menit (MP4) | video demo final | 5 |
| [disediakan tim] screenshot Telegram 06.30 | pesan peringatan di HP | 4 |
| [disediakan tim, opsional] gambar dari video (Bu Sri, lantai jemur) | ilustrasi suasana | 2, 11 |

Untuk slide 5: siapkan slide penuh dengan bingkai video. Kalau ppt-master tidak bisa menanam video, pasang gambar `dasbor_0630_berpotensi.png` sebagai poster dan beri catatan "sisipkan MP4 lewat Insert → Video di PowerPoint" di speaker notes.

## Sumber (kaki slide)

APJII (2025) Survei Penetrasi Internet Indonesia · Bapanas (2025) Kepka No. 14/2025 · Bevis dkk. (1992) JGR 97(D14) · BMKG (2026) Prakiraan Musim Hujan 2026/2027 · BPS (2023) Sensus Pertanian 2023 · BPS (2026) Produksi padi 2025 · Ditjen PPHP (2008) Susut panen dan pascapanen padi · Hersbach dkk. (2020) ERA5 · Huffman dkk. (2023) GPM IMERG V07 · InfoPublik (18 Mar 2026) · Saastamoinen (1972) · Wijaya dkk. (2024) Adv. Space Res. 73(1) · rtklibexplorer (2025) RTKLIB-EX 2.5.1 · CODE (2026) produk MGEX lewat NASA CDDIS.
