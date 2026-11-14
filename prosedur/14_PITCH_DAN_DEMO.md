# Pitch, video, dan demo

Ketentuan Tech Meeting: presentasi **5 menit + 1 menit video** di panggung, dari laptop panitia. Yang wajib dibahas: **latar belakang pemilihan isu, metodologi, hasil, dan penyelesaian masalah**. Penilaian 5 × 20%: kesesuaian tema, prototipe fungsional (dibuktikan video 1 menit), inovasi futuristik (5–10 tahun), kesiapan presentasi, kesiapan demonstrasi.

Kaitan menarik: **stasiun BAKO berada di kompleks BIG Cibinong**, tempat Demo Day. Kalau stream BAKO jalan, kalimat pembuka saat validasi meja atau di panggung bisa: "Uap air yang kami ukur sekarang berasal dari antena GNSS di kompleks ini."

## Naskah 5 menit

| Waktu | Bagian | Isi pokok | Kriteria |
|---|---|---|---|
| 0:00–0:40 | Isu | Bu Sri dan gabahnya; susut penjemuran 3,59%, skala hingga Rp16,8 triliun per tahun; musim hujan mundur di 61% wilayah | tema |
| 0:40–1:15 | Insight | 474 stasiun Ina-CORS sudah "mencium" uap air tiap detik; belum ada yang mengubahnya jadi keputusan angkat atau tunggu | tema, inovasi |
| 1:15–2:15 | Metodologi | RINEX → PPP GPS+GLONASS → ZTD → PWV → persentil 15 hari per stasiun → pesan Telegram dengan aturan sopan (06–18, maks 2/hari, aman lagi s.d. 15.00) | presentasi |
| (video) | Bukti | putar video 1 menit | prototipe |
| 2:15–3:15 | Hasil | HSS 0,32 vs 0,18 (bermakna), 0,44 notifikasi/hari; jujur: "kemarin hujan" 0,40, gabungan 0,42 jadi versi 2; multi-GNSS 26,8% vs 0,3% saat langit terhalang | prototipe, tema |
| 3:15–4:15 | Penyelesaian masalah | ambang mutlak gagal di Lembang → persentil per stasiun; tanpa koreksi orbit PWV meleset 9–14 mm → koreksi SSR real-time; stream BIG terganggu → BAKO lewat IGS; biaya komponen Rp0 | presentasi |
| 4:15–5:00 | Masa depan | 5–10 tahun: receiver murah di balai desa, asimilasi PWV, indeks asuransi; kuadran dampak tinggi–layak; kalimat penutup | inovasi |

Kalimat penutup (contoh): "Infrastrukturnya sudah ada di 474 titik. AngkatDulu membuatnya bicara dalam bahasa yang dimengerti Bu Sri: angkat dulu, atau jemur lagi."

Pembagian pembicara (maksimal 3): pembicara 1 isu + insight, pembicara 2 metodologi + hasil, pembicara 3 penyelesaian masalah + masa depan. Semua anggota naik panggung.

## Kerangka slide

| # | Judul | Isi visual |
|---|---|---|
| 1 | AngkatDulu | nama tim, tagline, logo |
| 2 | Lima menit untuk menyelamatkan gabah | foto/ilustrasi lantai jemur, 3 angka besar (3,59%, Rp16,8 T, 61%) |
| 3 | Sensor yang sudah ada | peta 474 Ina-CORS, ilustrasi sinyal melewati uap air |
| 4 | Cara kerja | Gambar 1 arsitektur (dari satelit ke Telegram) |
| 5 | Video 1 menit | video tertanam |
| 6 | Hasil uji | tabel HSS 5 aturan + Gambar 3 replay 24–25 Okt |
| 7 | Multi-GNSS | 8,7 → 14,0 satelit; 26,8% vs 0,3% |
| 8 | Masalah yang kami pecahkan | 3–4 kartu: masalah → solusi |
| 9 | Tech stack dan biaya | dari [08_TECH_STACK.md](08_TECH_STACK.md), Rp0 komponen |
| 10 | 5–10 tahun lagi | matriks kelayakan–dampak + peta jalan 4 tahap |
| 11 | Terima kasih | kontak, QR bot Telegram |

## Video 1 menit

Semua cuplikan replay diberi label "Replay data 25 Okt 2026" di layar.

| Detik | Gambar | Teks/suara |
|---|---|---|
| 0–8 | lantai jemur gabah, langit mendung | "Bu Sri punya beberapa menit sebelum hujan." |
| 8–18 | dashboard: 4 stasiun, grafik PWV CKRG naik melewati garis persentil 80 | "Stasiun GNSS di Karawang mencatat uap air naik." |
| 18–28 | status berubah BERPOTENSI 06.30; HP berbunyi, pesan Telegram muncul | "AngkatDulu mengirim peringatan 3 jam sebelumnya." |
| 28–38 | grafik: hujan IMERG mulai 07.30; panel log pesan | "Satu jam kemudian hujan turun." |
| 38–46 | HP: "Tadi hujan?" → tekan "Hujan" | "Jawaban petani mengalibrasi ulang ambang." |
| 46–54 | ubin 4 stasiun di dashboard (panel live BAKO bila stream jalan) | "Multi-GNSS, data Ina-CORS, tanpa sensor baru." |
| 54–60 | logo + tagline | "AngkatDulu. Angkat dulu, jemur lagi." |

Teknis: rekam layar laptop (dashboard) dan layar HP terpisah, gabungkan; resolusi 1920×1080, MP4 H.264, tanpa musik berhak cipta. Siapkan juga versi GIF tanpa suara.

Cara merekam:

1. `python demo_bot.py --replay --detik-per-tick 3`, daftarkan HP, tunggu dashboard menampilkan **Siap diputar**.
2. Browser layar penuh (F11). Mulai rekam layar laptop (Win+Alt+R) dan rekam layar HP.
3. Tekan **Mulai replay**. Dengan 3 detik per 30 menit, 05.00–09.00 selesai dalam ±25 detik; jeda di 06.30 dan 08.00 bila perlu momen HP berbunyi yang lebih panjang, lalu potong di penyuntingan.
4. Di HP, tekan **Hujan** saat "Tadi hujan?" datang; jawaban muncul di panel pesan.
5. Ulangi dengan **Putar ulang** bila ada yang kurang pas; tiap putaran sesi baru, HP menerima pesan lagi.

## Di mana penilaian terjadi

| Waktu | Siapa yang melihat | Yang dinilai atau dilihat | Persiapan |
|---|---|---|---|
| 09.40–09.50 | panitia BIG keliling meja | validasi konsep; kesiapan perangkat | sistem sudah menyala sebelum 09.40, penjelasan 1 menit, semua perangkat di meja |
| 10.00–10.30 (urutan 5) | juri, di panggung | presentasi 5 menit + video 1 menit (tema, prototipe, inovasi, kesiapan presentasi) | naskah dan video, lihat di atas |
| 13.30–14.30 | peserta lain dan tamu (juri sedang rapat tertutup) | tidak dinilai | demo santai untuk jejaring, terutama dengan staf BIG |

Artinya juri tidak menyentuh prototipe secara langsung. **Video harus berdiri sendiri** sebagai bukti prototipe berfungsi: perlihatkan sistem sungguhan (layar dashboard, HP yang menerima pesan), bukan animasi.

## Validasi konsep di meja (09.40–09.50)

- **Penjelasan 1 menit**: masalah → cara kerja → bukti → angka utama.
- **Yang sudah menyala di layar**: dashboard replay 25 Okt dipercepat, HP "Bu Sri" dengan pesan Telegram terbaru, dan (bila jalan) panel live BAKO.
- **Bahan cetak**: satu lembar ringkasan (arsitektur + tabel hasil) yang bisa ditinggal di meja.

## Meja pukul 13.30–14.30

Pengunjung adalah peserta lain dan tamu. Biarkan mereka menekan "Tadi hujan?" sendiri di HP demo. Tidak dinilai, tetapi baik untuk jejaring dan masukan.

## Checklist perangkat (kesiapan demonstrasi 20%)

- [ ] Laptop demo + charger, sudah diuji replay tanpa internet
- [ ] HP "Bu Sri" dengan Telegram, terdaftar ke bot, baterai penuh
- [ ] HP cadangan untuk hotspot internet
- [ ] Power bank, terminal/colokan cabang
- [ ] Adaptor HDMI/USB-C dan kabel penghubung (disebut di kriteria kesiapan demonstrasi)
- [ ] Flashdisk: PPT, PDF, MP4, GIF
- [ ] `config\.env` terisi (token bot, akun NTRIP), tidak ikut di flashdisk
- [ ] BNC atau `rtkrcv` terpasang dan terkonfigurasi untuk BAKO
- [ ] Database `angkatdulu.db` sudah dibangun, `pytest` lulus
- [ ] Cetak ringkasan satu lembar

---

Kembali ke [indeks](00_README.md).
