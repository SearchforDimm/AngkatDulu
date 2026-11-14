# Latar belakang: kenapa AngkatDulu ada

## Cerita Bu Sri

Bagi kebanyakan orang, jemuran kehujanan berarti baju dicuci ulang. Lain ceritanya dengan **Bu Sri** (persona ilustratif), petani gabah di Jayakerta, Karawang, yang menghamparkan gabah hasil kerja empat bulan di lantai jemur depan rumah. Begitu langit tiba-tiba gelap, ia hanya punya beberapa menit untuk menyapu gabah dan menutupnya dengan terpal, sering kali sendirian.

Yang dibutuhkan Bu Sri adalah satu keputusan sederhana: **angkat sekarang atau tunggu**. Bukan peta cuaca, bukan istilah meteorologi.

## Besar masalahnya

| Fakta | Angka | Sumber |
|---|---|---|
| Susut padi saat penjemuran | 3,59% | Ditjen PPHP, Kementerian Pertanian (2008) |
| Produksi padi 2025 | 71,95 juta ton GKP | BPS (2026) |
| Harga Pembelian Pemerintah gabah | Rp6.500/kg | Bapanas (2025) |
| Nilai susut penjemuran (batas atas) | ±Rp16,8 triliun per tahun | hitungan dari tiga baris di atas |
| Per petani berlahan 0,5 ha | ±Rp742 ribu per panen | hitungan yang sama |
| Awal musim hujan 2026/2027 mundur | 61,08% daratan Indonesia | BMKG (2026) |
| Rumah tangga usaha pertanian | 28,4 juta (16,89 juta petani gurem) | Sensus Pertanian 2023, BPS |
| Rumah tangga tanaman pangan / perkebunan | 15,55 juta / 10,88 juta | BPS (2023) |
| Penetrasi internet perdesaan | 76,96% | APJII (2025) |

Catatan kejujuran: tidak semua susut disebabkan hujan, dan sebagian petani menjual gabah basah ke penebas. Angka Rp16,8 triliun hanya menunjukkan **skala masalah**, belum manfaat AngkatDulu. Sasaran kami adalah rumah tangga yang masih menjemur sendiri, termasuk pengolah ikan asin di Roban Timur, Batang, yang bisa merugi jutaan rupiah saat hujan atau mendung (Mongabay, 2025).

Musim peralihan yang panjang membuat masalah ini makin terasa: hujan bisa turun di sela hari-hari cerah, justru saat petani paling berani menjemur.

## Celah yang diisi

- **Peringatan BMKG** (*nowcasting* 0–6 jam) menggambarkan cuaca per wilayah dan tidak dirancang sebagai saran tindakan bagi penjemur.
- **Radar cuaca BMKG** baru 44 unit per Maret 2026 (InfoPublik, 2026), sementara banyak sentra pertanian di luar jangkauannya.
- **474 stasiun Ina-CORS milik BIG** sudah merekam sinyal satelit setiap detik, dan sinyal itu melambat sebanding dengan uap air yang dilewatinya. Datanya belum diolah menjadi pesan untuk orang yang sedang menjemur.

## Kenapa GNSS

- **Sudah ada**: tidak perlu sensor baru, biaya komponen prototipe Rp0.
- **Mengukur uap air sebelum awan hujan terbentuk**: PWV naik sebelum hujan konvektif, sedangkan radar baru melihat butir hujan.
- **Tersedia di wilayah tanpa radar**, terus-menerus, siang dan malam, dalam segala cuaca.
- **Dasar ilmiahnya mapan** sejak Bevis dkk. (1992); di Indonesia, PWV Ina-CORS berbeda 2,59 mm (RMSD) dari ERA5 (Wijaya dkk., 2024).
- **Sesuai tema multi-GNSS**: GPS + GLONASS membuat ZTD tetap tersedia saat sebagian langit terhalang (lihat [06_KALIBRASI_DAN_HASIL.md](06_KALIBRASI_DAN_HASIL.md)).

## Posisi terhadap layanan yang sudah ada

- **Modul ZWD real-time SRGI** sudah menghitung ZWD tiap stasiun. AngkatDulu bekerja di hilirnya: ZWD → PWV → keputusan di HP petani.
- **BMKG**: AngkatDulu melengkapi, bukan menggantikan. Pesannya selalu menyebut stasiun dan jarak, dan rekam jejaknya terbuka.

## Kebaruan

Kontribusi kami ada pada rantai yang utuh dari ZWD sampai keputusan di lantai jemur:

1. Ambang per stasiun (persentil 15 hari terakhir), karena ambang mutlak gagal di dataran tinggi.
2. Kebijakan pesan yang menghormati penerima: hanya 06.00–18.00, maksimal 2 notifikasi per hari, "aman lagi" hanya sampai 15.00.
3. Rekam jejak terbuka di setiap pesan, dan jawaban "Tadi hujan?" untuk mengalibrasi ulang ambang.

## Daftar pustaka

- APJII. (2025). *Survei Penetrasi Internet Indonesia 2025*.
- Badan Informasi Geospasial. (2025). *Rencana Strategis BIG 2025–2029*. Data RINEX Ina-CORS: srgi.big.go.id.
- Badan Pangan Nasional. (2025). Keputusan Kepala Badan Pangan Nasional Nomor 14 Tahun 2025 (HPP dan rafaksi harga gabah dan beras).
- BPS. (2023). *Hasil Pencacahan Lengkap Sensus Pertanian 2023*.
- BPS. (2026). Luas panen dan produksi padi di Indonesia 2025 (angka tetap). Berita Resmi Statistik, 2 Februari 2026.
- Benevides, P., Catalão, J., & Miranda, P. M. A. (2015). On the inclusion of GPS precipitable water vapour in the nowcasting of rainfall. *NHESS*, 15, 2605–2616.
- Bevis, M., dkk. (1992). GPS meteorology: Remote sensing of atmospheric water vapor using the Global Positioning System. *JGR*, 97(D14), 15787–15801.
- Bevis, M., dkk. (1994). GPS meteorology: Mapping zenith wet delays onto precipitable water. *J. Appl. Meteorol.*, 33(3), 379–386.
- BMKG. (2026). *Prakiraan Musim Hujan 2026/2027 di Indonesia*.
- CODE. (2026). Produk orbit dan jam presisi MGEX dan rapid, melalui NASA CDDIS.
- Ditjen PPHP, Departemen Pertanian. (2008). Data susut panen dan pascapanen padi.
- Hersbach, H., dkk. (2020). The ERA5 global reanalysis. *QJRMS*, 146(730), 1999–2049.
- Huffman, G. J., dkk. (2023). GPM IMERG Late Precipitation L3 Half Hourly V07. NASA GES DISC.
- InfoPublik. (2026, 18 Maret). HMD 2026, BMKG perkuat sistem observasi untuk lindungi masa depan.
- Landskron, D., & Böhm, J. (2018). VMF3/GPT3: Refined discrete and empirical troposphere mapping functions. *J. Geod.*, 92(4), 349–360.
- Mongabay. (2025, 13 Juli). Cerita perempuan nelayan terdampak PLTU Batang.
- Richardson, D. S. (2000). Skill and relative economic value of the ECMWF ensemble prediction system. *QJRMS*, 126(563), 649–667.
- rtklibexplorer. (2025). RTKLIB-EX 2.5.1. github.com/rtklibexplorer/RTKLIB.
- Saastamoinen, J. (1972). Atmospheric correction for the troposphere and stratosphere in radio ranging of satellites. *Geophysical Monograph 15*, 247–251.
- Weber, G., Dettmering, D., & Gebhard, H. (2005). Networked Transport of RTCM via Internet Protocol (NTRIP). *IAG Symposia*, 128, 60–64. (wajib dikutip bila memakai data IGS-IP dalam publikasi)
- Wijaya, D. D., dkk. (2024). Determination and assessment of GNSS-derived precipitable water vapor in Indonesia using Ina-CORS. *Adv. Space Res.*, 73(1), 386–403.

---

Kembali ke [indeks](00_README.md).
