| kode   | besaran                                                               | nilai        | keterangan                                    |
|:-------|:----------------------------------------------------------------------|:-------------|:----------------------------------------------|
| PPP    | Satelit per epoch, GPS saja                                           | 9,2          | 18–28 Okt, PPP-fixed harian                   |
| PPP    | Satelit per epoch, GPS + GLONASS                                      | 15,1         | 18–28 Okt, PPP-fixed harian                   |
| PPP    | Sigma ZTD, GPS saja (mm)                                              | 4,1          | rata-rata setelah 1 jam pertama tiap hari     |
| PPP    | Sigma ZTD, GPS + GLONASS (mm)                                         | 3,5          | idem                                          |
| PWV    | PWV rata-rata harian 19 Okt (mm)                                      | 30,7         | hari UTC                                      |
| PWV    | PWV rata-rata harian 24 Okt (mm)                                      | 50,1         | hari UTC                                      |
| PWV    | PWV rata-rata harian 27 Okt (mm)                                      | 60,4         | hari UTC                                      |
| PWV    | Kenaikan 19→24 Okt (mm)                                               | 19,4         |                                               |
| SENS   | Selisih PWV, met. konstan vs ERA5: RMS (mm)                           | 0,64         | meniru model empiris tanpa variasi harian     |
| SENS   | Selisih PWV, met. konstan vs ERA5: maks (mm)                          | 1,82         |                                               |
| S-45   | Tabel kontingensi H/F/M/CN                                            | 42/214/4/266 | slot 30 menit serentak, 18–28 Okt             |
| S-45   | Waktu menyala                                                         | 49%          |                                               |
| S-45   | POD                                                                   | 0,91         |                                               |
| S-45   | FAR                                                                   | 0,84         |                                               |
| S-45   | CSI                                                                   | 0,16         |                                               |
| S-45   | HSS                                                                   | 0,15         |                                               |
| S-45   | Waktu menyala 24–28 Okt WIB                                           | 87%          | bukti ambang tetap mendeteksi musim lembap    |
| P-3J   | Ambang tetap PWV ≥ 45 mm: waktu menyala                               | 66%          | 21 Oct 08:00–29 Oct 03:30 WIB                 |
| P-3J   | Ambang tetap PWV ≥ 45 mm: POD                                         | 0,82         |                                               |
| P-3J   | Ambang tetap PWV ≥ 45 mm: FAR                                         | 0,69         |                                               |
| P-3J   | Ambang tetap PWV ≥ 45 mm: CSI                                         | 0,29         |                                               |
| P-3J   | Ambang tetap PWV ≥ 45 mm: HSS                                         | 0,14         |                                               |
| E-3J   | Ambang tetap PWV ≥ 45 mm: awal hujan diperingatkan                    | 1/5          | peringatan baru 0–3 jam sebelum awal hujan    |
| E-3J   | Ambang tetap PWV ≥ 45 mm: lead time median (menit)                    | 60           |                                               |
| P-3J   | Anomali PWV ≥ 5 mm: waktu menyala                                     | 79%          | 21 Oct 08:00–29 Oct 03:30 WIB                 |
| P-3J   | Anomali PWV ≥ 5 mm: POD                                               | 0,88         |                                               |
| P-3J   | Anomali PWV ≥ 5 mm: FAR                                               | 0,72         |                                               |
| P-3J   | Anomali PWV ≥ 5 mm: CSI                                               | 0,27         |                                               |
| P-3J   | Anomali PWV ≥ 5 mm: HSS                                               | 0,07         |                                               |
| E-3J   | Anomali PWV ≥ 5 mm: awal hujan diperingatkan                          | 1/5          | peringatan baru 0–3 jam sebelum awal hujan    |
| E-3J   | Anomali PWV ≥ 5 mm: lead time median (menit)                          | 90           |                                               |
| P-3J   | Kenaikan ΔPWV ≥ 4 mm/3 jam: waktu menyala                             | 38%          | 21 Oct 08:00–29 Oct 03:30 WIB                 |
| P-3J   | Kenaikan ΔPWV ≥ 4 mm/3 jam: POD                                       | 0,35         |                                               |
| P-3J   | Kenaikan ΔPWV ≥ 4 mm/3 jam: FAR                                       | 0,77         |                                               |
| P-3J   | Kenaikan ΔPWV ≥ 4 mm/3 jam: CSI                                       | 0,16         |                                               |
| P-3J   | Kenaikan ΔPWV ≥ 4 mm/3 jam: HSS                                       | -0,03        |                                               |
| E-3J   | Kenaikan ΔPWV ≥ 4 mm/3 jam: awal hujan diperingatkan                  | 2/5          | peringatan baru 0–3 jam sebelum awal hujan    |
| E-3J   | Kenaikan ΔPWV ≥ 4 mm/3 jam: lead time median (menit)                  | 15           |                                               |
| P-3J   | Baseline pola harian (13.00–17.00 WIB): waktu menyala                 | 17%          | 21 Oct 08:00–29 Oct 03:30 WIB                 |
| P-3J   | Baseline pola harian (13.00–17.00 WIB): POD                           | 0,20         |                                               |
| P-3J   | Baseline pola harian (13.00–17.00 WIB): FAR                           | 0,70         |                                               |
| P-3J   | Baseline pola harian (13.00–17.00 WIB): CSI                           | 0,14         |                                               |
| P-3J   | Baseline pola harian (13.00–17.00 WIB): HSS                           | 0,04         |                                               |
| E-3J   | Baseline pola harian (13.00–17.00 WIB): awal hujan diperingatkan      | 0/5          | peringatan baru 0–3 jam sebelum awal hujan    |
| E-3J   | Baseline pola harian (13.00–17.00 WIB): lead time median (menit)      | n/a          |                                               |
| P-3J   | Baseline persistensi (hujan kemarin): waktu menyala                   | 14%          | 21 Oct 08:00–29 Oct 03:30 WIB                 |
| P-3J   | Baseline persistensi (hujan kemarin): POD                             | 0,15         |                                               |
| P-3J   | Baseline persistensi (hujan kemarin): FAR                             | 0,74         |                                               |
| P-3J   | Baseline persistensi (hujan kemarin): CSI                             | 0,10         |                                               |
| P-3J   | Baseline persistensi (hujan kemarin): HSS                             | 0,01         |                                               |
| E-3J   | Baseline persistensi (hujan kemarin): awal hujan diperingatkan        | 1/5          | peringatan baru 0–3 jam sebelum awal hujan    |
| E-3J   | Baseline persistensi (hujan kemarin): lead time median (menit)        | 30           |                                               |
| E-3J   | Jumlah awal hujan                                                     | 5            | ≥ 1 mm/jam setelah ≥ 3 jam < 0,2 mm/jam       |
| V      | Rentang C/L dengan V > 0                                              | 0,14–0,31    | P-3J ambang 45 mm                             |
| V      | V maksimum                                                            | 0,21         | pada C/L ≈ 0,25                               |
| V      | Frekuensi dasar hujan 3 jam (s̄)                                      | 0,25         |                                               |
| EKO    | K_nasional basis GKP (Rp triliun)                                     | 16,8         | Q × j × s × P, j = 1 (batas atas)             |
| EKO    | K_nasional basis GKG (Rp triliun)                                     | 17,3         | harga GKG Rp8.000/kg                          |
| EKO    | Susut per petani 0,5 ha per panen (kg)                                | 114          | produktivitas 6,36 t GKP/ha                   |
| EKO    | Susut per petani 0,5 ha per panen (Rp ribu)                           | 742          |                                               |
| EKO    | K_terhindar per 1.000 pengguna per panen, r = 0.25, e = 0,2 (Rp juta) | 37           | asumsi ilustratif; u = 1 untuk pengguna pilot |
| EKO    | K_terhindar per 1.000 pengguna per panen, r = 0.5, e = 0,2 (Rp juta)  | 74           | asumsi ilustratif; u = 1 untuk pengguna pilot |