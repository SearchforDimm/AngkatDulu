# Catatan desain dashboard AngkatDulu

Berlaku untuk `dasbor/index.html`. Hanya tampilan; kontrak data dengan `dasbor/server.py` tidak berubah.

## Untuk siapa dan di mana

Juri BIG (ahli geodesi) menonton lewat video 1920×1080 di proyektor, dan panitia melihat langsung di meja.
Pesan utama harus terbaca dari jauh dalam 2–3 detik. Ruangan terang dan proyektor memucatkan warna muda,
jadi tema terang dengan bidang warna pekat, bukan tema gelap.

## Kritik tampilan sebelumnya

1. Jam (kotak hitam, 72 px) lebih menonjol daripada status, padahal status adalah pesan utamanya.
2. Status hanya dibedakan lewat latar pucat dan garis warna di tepi kiri. Dari jauh, WASPADA dan BERPOTENSI mirip.
3. Momen 06.30 tidak terasa: kelas CSS berganti tanpa gerak, dan titik perpotongan di grafik tidak ditandai.
4. Teks grafik 12 px (label ujung garis, sumbu, tanda pesan) tidak terbaca di proyektor.
5. Isi pesan dipotong 3 baris, padahal seharusnya tampil utuh.
6. Animasi pesan baru terputus setelah 0,6 detik karena daftar dibangun ulang tiap polling.
7. Lencana Replay kecil dan bergaris tipis, dan jam tidak diberi keterangan "simulasi".
8. Pita TANPA_DATA tidak ada di legenda.

## Arah: papan peringatan di lantai jemur

Satu arah, mempertajam identitas yang sudah ada (semen lantai jemur, biru terpal, tinta hijau-hitam).

1. **Pita status selebar layar.** Jam simulasi, status, dan rel waktu replay ada di satu pita warna dari tepi ke tepi
   layar, tanpa kotak jam terpisah. Kerasnya warna mengikuti gentingnya status: AMAN hijau muda dan tenang,
   WASPADA amber pekat, BERPOTENSI merah pekat dengan teks putih, TANPA_DATA abu berarsir. Ikon dan teks selalu ikut.
   Di bawah pita ada rel waktu: awal dan akhir replay, satu takik tiap jam, dan kepala putar di jam simulasi.
   Kepala halaman satu baris: merek, lencana Replay, keterangan bot, lalu tombol utama dan kecepatan sebagai
   satu kendali pemutar (ikon main, jeda, atau putar ulang mengikuti fase).
2. **Skala huruf bertingkat.** Ukuran dasar 18 px di 1920×1080, 16 px di layar sedang, 14 px di 1366×768.
   Judul status 61 px dan jam 101 px di 1920×1080. Semua angka tabular.
3. **Grafik terbaca dari jauh.** Garis PWV ±3,8 px dan teks grafik 15 px di 1920×1080 (ikut skala huruf halaman),
   pita status diberi rel warna pekat di atasnya,
   dan arsiran di luar jam jemur digambar di atas pita supaya tetap terlihat.
4. **Momen 06.30 ditandai.** Tiap pesan BERPOTENSI/AMAN_LAGI punya garis bendera, cincin di titik kurva PWV pada jam itu,
   dan label pil (pekat = dikirim, garis = ditahan).
5. **Tiga isyarat gerak, satu peristiwa.** Saat status berganti: warna lama diusap warna baru di papan,
   cincin berdenyut dua kali di grafik, dan pesan baru masuk dengan sorotan. Tidak ada gerak lain.
   Semuanya mati di `prefers-reduced-motion`.
6. **Log seperti layar HP.** Isi pesan utuh di dalam gelembung, diwarnai menurut jenis pesan.
   Jawaban Bu Sri tampil sebagai gelembung balasan biru terpal di kanan. Pesan ditahan tampil sebagai kotak bergaris putus.
7. **Kejujuran replay.** Lencana "Replay data …" pekat di kepala halaman, dan "jam simulasi" menempel di samping jam.
8. **Yang sekunder mundur.** Ubin stasiun dan rekam jejak memakai bidang tembus di atas semen; ubin terpilih putih bergaris tinta.

## Revisi bagian atas

Versi pertama memakai kotak jam hitam di samping kartu status. Hasilnya terasa kaku, karena:

- kotak jam mengikuti pola kartu metrik (angka besar, label kecil, bar progres);
- lingkaran play biru di fase SIAP tampak seperti tombol padahal tidak bisa diklik;
- kendali replay tersebar di tiga tempat (lencana, tombol dan kecepatan, kotak jam);
- keterangan bot dua baris menggantung, dan dropdown kecepatan masih bergaya bawaan browser;
- di laptop dengan bilah browser (1366×643) bagian atas memakan 188 px dan grafik hanya 211 px.

Sekarang kepala dan pita setinggi 150 px di ukuran itu, grafik 240 px, dan ikon fase SIAP berupa panah putar ulang.

## Token

| Peran | Nilai | Kontras (dihitung) |
|---|---|---|
| Latar semen | `#e4e6e0` | tinta 3 di atas semen 4,7 |
| Tinta / tinta 2 / tinta 3 | `#17201a` / `#47504a` / `#5f675f` | 16,7 / 8,4 / 5,9 di atas putih |
| Biru terpal (garis PWV, tombol, balasan) | `#1e6fd1` | 4,9 dengan teks putih |
| AMAN | `#1a7f37`, muda `#dcefdc` | teks papan 13,9 dan 8,2; label putih 5,1 |
| WASPADA | `#f5b223`, tua `#8f6200`, muda `#fdefc8` | teks papan 9,0 dan 6,8; amber tua di putih 5,4 |
| BERPOTENSI | `#c8322f`, muda `#f8dedb` | 5,3 dengan teks putih |
| TANPA_DATA | `#69716a`, muda `#e9ebe6` | 5,0 dengan teks putih; ikon di bidang muda 4,2 |

Huruf: tumpukan font sistem yang sudah ada. Bahnschrift (lebar 87,5–90%) untuk jam dan judul, Segoe UI untuk teks.
Tidak ada font, pustaka, atau gambar dari luar.

## Dari skill

- **ui-ux-pro-max** menyarankan pola "real-time/operations": status hijau, amber, merah di atas netral, label waktu nyata
  hanya bila datanya memang nyata, garis berbeda gaya (utuh, putus, titik) dengan label langsung, anomali ditandai bentuk
  dan teks, dan paling banyak 1–2 elemen bergerak. Saran tema gelap OLED dan Fira dari Google Fonts tidak dipakai,
  karena proyektor di ruang terang dan syarat tanpa internet.
- **impeccable** (mode Operate, kritik lalu polish): tidak memakai garis warna tebal di tepi kartu, tidak memakai label kecil
  di atas judul, teks sekunder di bidang berwarna diwarnai dari rona bidangnya, satu momen gerak yang disengaja,
  dan permukaan bawaan browser (seleksi, scrollbar, cincin fokus) ikut palet.

## Pengecualian yang disengaja

- Detektor impeccable melaporkan "flat type hierarchy" karena ukuran judul diatur lewat variabel CSS dan terbaca 16 px
  secara statis. Hasil render: judul status 61 px, jam 101 px, judul panel 23 px, teks 18 px (di 1920×1080).
- Arsiran garis miring di papan TANPA_DATA bukan hiasan. Pola yang sama dipakai di pita grafik dan legenda,
  supaya "tanpa data" tidak dibaca hanya dari warna abu.

## Batas

Tidak ada endpoint, field, atau angka baru. Semua posisi dan nilai di grafik berasal dari `/api/keadaan`.
Bagian halaman yang isinya tidak berubah tidak dibangun ulang tiap polling 600 ms, supaya animasi dan fokus tidak terputus.
Polling dan kontraknya sendiri tetap sama.
