# Rencana kerja sampai Demo Day

Disusun dari to-do tim dan ketentuan Tech Meeting (12 Nov 2026). Status per **Jumat 13 Nov 2026 malam** (bot dan dashboard selesai).

## Tenggat dari panitia

| Kapan | Apa | Catatan |
|---|---|---|
| **Senin 16 Nov, 23.59 WIB** | Kirim materi presentasi ke `kerjasama@big.go.id` | PPT/PDF + video 1 menit (atau .gif), atau PPT yang sudah berisi video. Subjek: "BIG Bhumireka 2026 – AngkatDulu". Presentasi diputar dari laptop panitia. |
| Kamis 19 Nov, 08.00 | Registrasi di BIG Cibinong, Bogor | |
| 09.40–09.50 | Persiapan di meja; panitia BIG keliling memvalidasi konsep | **satu-satunya kesempatan pihak BIG melihat langsung di meja**: penjelasan 1 menit, sistem sudah menyala, semua perangkat terlihat |
| **10.00–10.30** | Presentasi tim 1–5; **AngkatDulu urutan ke-5** | 5 menit + 1 menit video; maksimal 3 orang bicara, semua anggota naik panggung |
| 13.30–14.30 | Tim berjaga di meja; juri rapat tertutup menetapkan nilai | pengunjung meja adalah peserta lain dan tamu, bukan juri; demo tetap jalan untuk jejaring |
| 14.30–14.45 | Pengumuman | |

Karena juri menilai saat presentasi di panggung (dan panitia melihat meja pukul 09.40), **video 1 menit adalah bukti utama prototipe fungsional di mata juri**.

**Jalur kritis**: token bot → bot Telegram → dashboard → rekam video → kirim **16 Nov**. Video harus memperlihatkan sistem yang sudah jalan, jadi bot dan dashboard harus selesai paling lambat **Minggu 15 Nov siang**.

## Prioritas untuk kiriman 16 Nov

Yang dikirim 16 Nov hanya **PPT/PDF + video 1 menit**. Semua yang tidak muncul di keduanya ditunda sampai sesudah 16 Nov.

| Urutan | Pekerjaan | Kapan | Siapa | Kenapa duluan |
|---|---|---|---|---|
| 1 | Buat bot di @BotFather, isi token di `config\.env` | Jum 13 malam / Sab 14 pagi | kamu | semua langkah sesudahnya tertahan di sini |
| 2 | Bot minimal: `/start` + lokasi, pesan BERPOTENSI / AMAN_LAGI / TANYA_HUJAN dengan tombol, label `[REPLAY]` | Sab 14 | Claude, uji di HP | adegan inti video |
| 3 | Dashboard minimal: status 4 stasiun, grafik PWV + ambang + hujan, log pesan, tombol putar replay | Sab 14 malam – Min 15 pagi | Claude | adegan inti video |
| 4 | Uji di laptop tanpa internet, lalu rekam video 1 menit sesuai storyboard | Min 15 | tim | bukti prototipe fungsional bagi juri |
| 5 | PPT 11 slide (draf Sab 14, final Sen 16 siang), video ditanam + PDF cadangan | Sab 14 – Sen 16 | tim + Claude | bahan presentasi |
| 6 | Kirim ke `kerjasama@big.go.id`: PPT, MP4 terpisah, PDF | **Sen 16 sebelum 20.00** | ketua | tenggat 23.59 |

Ditunda sesudah 16 Nov: panel live di dashboard, latihan tanya jawab, checklist perangkat, live BAKO, perbandingan PWV BIG, ML.

Bisa dikerjakan tim sambil menunggu langkah 2–3: kerangka dan visual PPT, foto atau video lantai jemur milik sendiri untuk 8 detik pertama video (jangan pakai rekaman berhak cipta), HP "Bu Sri" dengan Telegram, aplikasi perekam layar (Win+Alt+R di Windows, perekam layar bawaan di HP).

## To-do

| # | Pekerjaan | Status | Target | Siapa |
|---|---|---|---|---|
| 1 | Dokumentasi cara kerja pengolahan data | **selesai** (folder `prosedur/`) | 13 Nov | Claude |
| 2 | Tech stack | **selesai** ([08_TECH_STACK.md](08_TECH_STACK.md)); tinggal jadi 1 slide | 13 Nov | Claude |
| 3 | Token bot Telegram di `config\.env` | **selesai** | **Sab 14 Nov pagi** | kamu |
| 4 | Bot Telegram ([spesifikasi](09_SISTEM_BOT_DASHBOARD.md)) | **selesai** 13 Nov, sudah diuji di HP | Sab 14 Nov | Claude, uji di HP kamu |
| 5 | Dashboard lokal (`dasbor/`, dibuka oleh `demo_bot.py --replay`) | **selesai** 13 Nov; tinggal dicoba di laptop | Min 15 Nov siang | Claude |
| 6 | Uji ujung-ke-ujung di laptop demo (replay 25 Okt, tanpa internet) | belum | Min 15 Nov siang | kamu + Claude |
| 7 | Video demo 1 menit ([storyboard](14_PITCH_DAN_DEMO.md#video-1-menit)) | belum | Min 15 Nov malam | tim (rekam layar + HP) |
| 8 | PPT pitch ([kerangka slide](14_PITCH_DAN_DEMO.md#kerangka-slide)) | belum | draf Sab 14, final Sen 16 siang | tim + Claude |
| 9 | Kirim PPT + video + PDF cadangan | belum | **Sen 16 Nov, sebelum 20.00** (cadangan waktu) | ketua |
| 10 | Latihan presentasi 5 menit dengan timer | belum | Sen 16 – Rab 18 | tim |
| 11 | Mode live BAKO (BNC → `rtkrcv`) | uji akun IGS | masuk video bila jalan sebelum Min 15; kalau tidak, tampilkan di meja saat validasi 09.40 | kamu + Claude |
| 12 | Bandingkan PWV kiriman BIG dengan PWV kita | menunggu data | begitu data datang | Claude |
| 13 | Checklist perangkat demo | belum | Rab 18 Nov | tim |
| 14 | Cek status 4 stasiun di nrtk.big.go.id | rutin | pagi 19 Nov | kamu |

## Jadwal harian

| Hari | Fokus |
|---|---|
| Jum 13 Nov (malam) | dokumentasi selesai; kamu buat bot di @BotFather |
| Sab 14 Nov | bot Telegram jalan di HP "Bu Sri"; draf PPT dan naskah |
| Min 15 Nov | dashboard; uji ujung-ke-ujung; rekam dan sunting video 1 menit |
| Sen 16 Nov | final PPT, latihan pertama, **kirim materi sebelum 20.00** |
| Sel 17 Nov | perbaikan kecil, latihan tanya jawab ([12_JUDGE_QA.md](12_JUDGE_QA.md)), coba live BAKO |
| Rab 18 Nov | gladi bersih dengan timer, checklist perangkat, isi daya semua perangkat |
| Kam 19 Nov | Demo Day |

## Risiko dan cadangan

| Risiko | Cadangan |
|---|---|
| Token bot terlambat | dashboard tetap bisa direkam; pesan ditampilkan di panel log |
| Stream BAKO atau koreksi SSR tidak jalan | video dan demo memakai replay; panel live hanya ditampilkan bila jalan |
| Internet di lokasi buruk | dashboard dan replay offline; hotspot HP untuk bot |
| Video tidak bisa diputar di laptop panitia | kirim MP4 terpisah dan versi GIF, selain video di dalam PPT |
| Waktu presentasi lewat 5 menit | latih dengan timer; siapkan versi singkat tiap bagian |

---

Kembali ke [indeks](00_README.md).
