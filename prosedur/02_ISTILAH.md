# Istilah dan pengertian

| Istilah | Arti |
|---|---|
| **GNSS** | Sistem satelit navigasi global: GPS (AS), GLONASS (Rusia), Galileo (Eropa), BeiDou (Tiongkok), QZSS (Jepang). |
| **Multi-GNSS** | Memakai lebih dari satu sistem sekaligus. Lebih banyak satelit → solusi lebih stabil, terutama saat sebagian langit terhalang. |
| **Ina-CORS** | Jaringan stasiun GNSS permanen milik BIG (±474 stasiun). Kita memakai CKRG, BAKO, CLBG, CJUR. |
| **SRGI** | Portal BIG (`srgi.big.go.id`) tempat mengunduh RINEX harian Ina-CORS. |
| **RINEX** | Format teks standar data pengamatan GNSS. SRGI menyediakan RINEX 2.11, interval 30 detik, tersedia H+1 sekitar 02.00 UTC (09.00 WIB). |
| **RTCM 3 / MSM** | Format biner untuk stream real-time. MSM5/MSM7 memuat pengamatan multi-GNSS lengkap. |
| **NTRIP, caster, mountpoint** | Protokol untuk mengalirkan RTCM lewat internet. *Caster* adalah servernya, *mountpoint* adalah nama satu stream (mis. `BAKO00IDN0`). |
| **Source table** | Daftar mountpoint di sebuah caster, termasuk format, sistem satelit, dan lokasi. |
| **PPP** | *Precise Point Positioning*: mengolah satu stasiun saja dengan orbit dan jam satelit presisi. Menghasilkan posisi dan keterlambatan troposfer. |
| **PPP-static** | PPP yang menaksir koordinat stasiun (dipakai sekali untuk mendapat koordinat tetap). |
| **PPP-fixed** | Istilah RTKLIB untuk PPP dengan **koordinat stasiun ditetapkan** (bukan "ambiguitas di-fix"). Karena posisi tidak ikut ditaksir, ZTD lebih stabil. |
| **SP3 / CLK** | File orbit (SP3, per 5 menit) dan jam satelit (CLK, per 30 detik) dari pusat analisis, di sini CODE. |
| **Final / rapid** | Produk final paling teliti tapi terbit ±2 minggu; rapid terbit H+1 dan sedikit kurang teliti. |
| **SSR** | *State Space Representation*: koreksi orbit, jam, dan bias satelit yang dialirkan real-time (mis. `SSRA00CNE0`). Pengganti SP3/CLK untuk mode live. |
| **ANTEX (`igs20.atx`)** | Kalibrasi pusat fase antena satelit dan receiver. |
| **Radome** | Kubah pelindung antena (mis. SCIS, LEIM, LEIS). Memengaruhi kalibrasi antena. |
| **FCN GLONASS** | Nomor kanal frekuensi tiap satelit GLONASS. Header RINEX 2.11 SRGI tidak memuatnya, jadi disisipkan oleh `siapkan_rinex.py`. |
| **ZTD** | *Zenith Total Delay*: keterlambatan total sinyal di arah zenit akibat troposfer (±2,5 m). |
| **ZHD** | *Zenith Hydrostatic Delay*: bagian ZTD akibat udara kering, dihitung dari tekanan (±2,3 m). |
| **ZWD** | *Zenith Wet Delay* = ZTD − ZHD: bagian akibat uap air (±0,2–0,3 m). |
| **PWV** | *Precipitable Water Vapor*: tebal air (mm) jika semua uap air di kolom udara diembunkan. Di Jawa barat umumnya 25–60 mm. |
| **Tm** | Suhu rata-rata berbobot atmosfer basah (K), dipakai untuk konversi ZWD → PWV. |
| **Π (Pi)** | Faktor konversi ZWD → PWV, ±0,16. |
| **ERA5** | Reanalisis cuaca ECMWF per jam, grid 0,25°. Dipakai untuk tekanan permukaan dan suhu 2 m. Terbit ±5 hari kemudian. |
| **IMERG** | Estimasi hujan satelit NASA GPM per 30 menit. Diunduh lewat Giovanni (IMERG Late V07). Dipakai hanya untuk kalibrasi dan evaluasi. |
| **Slot** | Satu blok waktu 30 menit. Slot *t* adalah [t, t+30 menit). |
| **Tick / τ (tau)** | Saat mesin mengambil keputusan, di akhir slot (t + 30 menit). |
| **Kausal** | Keputusan di τ hanya memakai data yang sudah tersedia sebelum τ. |
| **Persentil** | Peringkat PWV 1 jam terakhir terhadap PWV 15 hari terakhir di stasiun yang sama (0–100). |
| **Histeresis** | Status tidak langsung padam saat syarat hilang, menunggu 60 menit, supaya tidak berkedip. |
| **Level** | AMAN, WASPADA (Level 1, persentil ≥ 65), BERPOTENSI (Level 2, persentil ≥ 80), TANPA_DATA. |
| **Awal hujan** | Slot pertama ≥ 0,2 mm/jam setelah ≥ 3 jam kering, dan kejadiannya mencapai puncak ≥ 1 mm/jam. |
| **P-3J** | Kebenaran per slot: ada hujan ≥ 1 mm/jam dalam 3 jam setelah τ. |
| **E-3J** | Awal hujan siang "tertangkap" bila ada notifikasi BERPOTENSI 0–3 jam sebelumnya. |
| **HSS** | *Heidke Skill Score*: 0 = setara tebakan acak, 1 = sempurna. Skor utama kita. |
| **POD / FAR** | *Probability of Detection* (hujan yang tertangkap) / *False Alarm Ratio* (peringatan yang meleset). |
| **LOSO** | *Leave-one-station-out*: ambang dipilih di 3 stasiun, diuji di stasiun ke-4, bergiliran. |
| **Bootstrap** | Pengambilan ulang hari-stasiun secara acak (2.000 kali) untuk menghitung selang kepercayaan 95%. |
| **Persistensi** | Pembanding "kemarin hujan di jam yang sama, hari ini hujan lagi". |
| **Pola harian** | Pembanding "waspada tiap 13.00–17.00 WIB". |
| **Rekam jejak** | Kalimat di pesan: "Bulan lalu di 4 stasiun, x dari n peringatan siang serupa diikuti hujan." |

---

Kembali ke [indeks](00_README.md).
