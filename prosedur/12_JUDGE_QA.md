# Perkiraan pertanyaan juri dan jawabannya

Disusun mengikuti 5 kriteria penilaian Tech Meeting (masing-masing 20%). Jawaban dibuat singkat, bisa diucapkan dalam 20–40 detik. Angka berasal dari [06_KALIBRASI_DAN_HASIL.md](06_KALIBRASI_DAN_HASIL.md).

Prinsip menjawab: sebut angkanya, sebut keterbatasannya kalau ada, lalu sebut langkah berikutnya. Jangan membesar-besarkan.

## A. Kesesuaian tema

**1. Di mana unsur multi-GNSS-nya?**
Kami memakai GPS dan GLONASS sekaligus. Satelit per epoch naik dari 8,7 ke 14,0 dan ketidakpastian ZTD turun dari 5,0 ke 4,3 mm. Manfaat terbesarnya keandalan: dalam simulasi langit terhalang (elevasi di bawah 30° dibuang), ZTD GPS saja gagal pada 26,8% epoch, GPS + GLONASS hanya 0,3%. Stream BAKO yang kami pakai untuk live sudah memuat Galileo dan BeiDou juga.

**2. Kenapa memilih isu jemuran, bukan banjir?**
Keputusannya sederhana dan sering (angkat atau tunggu), kerugiannya terukur (susut 3,59%), dan penggunanya jutaan rumah tangga. Data uap air yang sama bisa dikembangkan untuk banjir kilat, tetapi itu butuh uji lebih lanjut, jadi kami jadikan irisan.

## B. Prototipe fungsional

**3. Apa yang sudah benar-benar jalan?**
RINEX → ZTD → PWV untuk 4 stasiun selama 2 bulan, kalibrasi terhadap hujan satelit, mesin peringatan dengan kebijakan pesan, dan replay yang lulus 17 uji otomatis. Bot Telegram dan dashboard yang ada di video adalah bagian yang kami selesaikan untuk Demo Day.

**4. Ini real-time atau tidak?**
Data RINEX SRGI terbit H+1, jadi demo utama memakai mode replay: data historis diputar seolah real-time, dan mesin tidak pernah melihat data masa depan (diuji otomatis). Untuk live, kami memakai stream BAKO lewat IGS dan koreksi orbit real-time. Kami sudah menguji bahwa tanpa koreksi orbit, PWV bisa meleset 9–14 mm, jadi koreksi itu wajib.

**5. Seberapa akurat PWV-nya?**
Literatur untuk Ina-CORS: 2,59 mm RMSD terhadap ERA5 (Wijaya dkk., 2024). PWV kami konsisten antarstasiun (korelasi CKRG–BAKO 0,886) dan sesuai ketinggian (Lembang paling kering).

**6. Bagaimana kalau stasiun mati?**
Bila data putus 2 jam, status menjadi TANPA_DATA dan tidak ada peringatan palsu. Pengguna otomatis dipasangkan ke stasiun sehat terdekat.

## C. Inovasi futuristik

**7. Apa yang baru? PWV dari GNSS kan sudah lama.**
Benar, dasarnya sejak Bevis dkk. 1992. Yang belum ada adalah rantai utuh dari jaringan geodetik nasional sampai keputusan di lantai jemur: ambang per stasiun, kebijakan pesan yang menghormati penerima, rekam jejak terbuka di setiap pesan, dan umpan balik "Tadi hujan?" untuk kalibrasi ulang.

**8. Seperti apa 5–10 tahun lagi?**
Receiver GNSS murah di balai desa menjadikan jaringan ini tingkat desa, PWV diasimilasikan ke model cuaca, dan indeks hujan dipakai untuk asuransi pertanian. Di matriks kelayakan–dampak, cara konvensional (radar baru) ada di kuadran dampak tinggi tetapi mahal; kami di kuadran dampak tinggi dan layak karena memakai infrastruktur yang sudah ada.

**9. Kenapa tidak pakai AI/ML?**
Data baru 2 bulan dan 66 awal hujan. Aturan yang bisa dijelaskan lebih jujur untuk tahap ini. Rencana ML sudah kami susun: dilatih dari data historis, input live hanya dari stream GNSS, dan baru dipakai kalau mengalahkan aturan sekarang (HSS 0,42).

## D. Kualitas hasil (sering muncul di presentasi)

**10. HSS 0,32 itu bagus?**
HSS 0 sama dengan menebak acak. 0,32 jauh di atas tebakan "waspada tiap sore" (0,18), dan selisihnya bermakna secara statistik (+0,14, selang 95% 0,05–0,23). Notifikasinya juga lebih jarang: 0,44 per hari dibanding 1,00.

**11. Tapi "kemarin hujan" malah lebih tinggi (0,40)?**
Ya, dan itu kami tampilkan apa adanya. Selisihnya belum bermakna. Gabungan PWV dengan "kemarin hujan" mencapai 0,42 dengan notifikasi paling sedikit (0,23 per hari), jadi itu aturan versi 2. PWV memberi sinyal fisik yang tidak dimiliki tebakan persistensi, misalnya di hari pertama hujan setelah kemarau.

**12. Berapa persen peringatan yang benar?**
39% jam status menyala diikuti hujan; 28% notifikasi diikuti hujan dalam 3 jam. Untuk penjemur, peringatan yang meleset hanya berarti menutup terpal sebentar, sedangkan hujan yang terlewat berarti gabah basah. Secara ekonomi aturan ini bernilai bila biaya bertindak 11–39% dari kerugian.

**13. Data 2 bulan cukup?**
Belum. Itu keterbatasan utama kami: satu peralihan musim, dan skor turun dari September ke Oktober (HSS 0,23). Karena itu ambang dikalibrasi per musim dan pilot tahun pertama dirancang untuk mengumpulkan data musim hujan.

**14. Bagaimana mencegah overfitting?**
Ambang dipilih dengan tiga stasiun lalu diuji di stasiun keempat secara bergiliran, ditambah uji September → Oktober dan bootstrap per hari-stasiun.

**15. Radius layanannya berapa?**
Belum terukur, dan kami tidak mengklaim angka. Jarak antarstasiun Ina-CORS ±60 km, sedangkan sel hujan beberapa kilometer, jadi setiap pesan menyebut jarak ke stasiun. Radius akan diukur dari jawaban "Tadi hujan?" saat pilot.

## E. Kesiapan presentasi dan demonstrasi

**16. Kenapa Telegram, bukan WhatsApp?**
Bot API Telegram gratis dan langsung bisa dipakai. WhatsApp resmi butuh verifikasi bisnis dan biaya per percakapan; masuk peta jalan. Penyuluh juga bisa meneruskan pesan ke grup WhatsApp desa.

**17. Berapa biayanya?**
Komponen prototipe Rp0 (data dan perangkat lunak terbuka). Operasional pilot ±Rp200 ribu per bulan.

**18. Bedanya dengan modul ZWD SRGI dan BMKG?**
SRGI sudah menghitung ZWD; kami bekerja di hilirnya, mengubahnya menjadi keputusan. BMKG memberi informasi cuaca per wilayah; kami memberi saran tindakan per titik jemur dengan rekam jejak terbuka. Kami melengkapi, bukan menggantikan.

**19. Bagaimana privasi lokasi pengguna?**
Lokasi dibulatkan ke ±100 m dan hanya dipakai untuk memilih stasiun terdekat.

**20. Kenapa tidak semua stasiun live?**
Stream khusus dari BIG sedang tidak tersedia karena gangguan server, jadi untuk live kami memakai BAKO yang juga dialirkan jaringan IGS. Tiga stasiun lain jalan dalam mode replay. Begitu stream BIG tersedia, sumbernya tinggal diganti; mesinnya sama.

---

Kembali ke [indeks](00_README.md).
