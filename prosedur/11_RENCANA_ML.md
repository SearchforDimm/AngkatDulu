# Rencana ML dan pengembangan lanjutan

Status: **rencana**, bukan untuk Demo Day. Prioritas sebelum 19 Nov adalah stream live, bot, dan dashboard.

## Bisakah model ML dilatih dari data historis lalu dipakai live?

Bisa, asal aturannya jelas: **data historis untuk melatih, input saat live hanya yang bisa dihitung dari stream GNSS.**

| Bagian | Isi |
|---|---|
| Label (target) | IMERG ≥ 1 mm/jam dalam 3 jam ke depan (hanya saat melatih) |
| Fitur live | PWV sekarang; perubahan PWV 1, 3, 6 jam; persentil 15 hari; jam dan hari dalam tahun; selisih PWV antarstasiun (uap air bergerak); opsional gradien troposfer dari RTKLIB |
| Fitur opsional | hujan terakhir dari IMERG Early (latensi ±4 jam) dan jawaban "Tadi hujan?" |
| Model awal | regresi logistik atau *gradient boosting* (LightGBM); bukan deep learning karena data sedikit |
| Keluaran | peluang hujan; ambang dipilih dari rasio biaya/kerugian seperti aturan sekarang |

## Masalah utama: data

PWV GNSS kita baru 2 bulan dengan 66 awal hujan. Dua cara menambah data:

1. **RINEX historis SRGI tahun-tahun sebelumnya** untuk 4 stasiun yang sama, diolah PPP. Paling bersih karena jenis datanya sama, tapi waktu prosesnya lama.
2. **ERA5 *total column water vapour* sebagai PWV tiruan** (per jam sejak 1940) dipasangkan dengan IMERG lebih dari 20 tahun. Datanya melimpah, tetapi:
   - ERA5 lebih halus (grid 0,25°), jadi lonjakan uap air sebelum hujan konvektif sering hilang.
   - Analisis ERA5 memakai observasi dalam jendela 12 jam, jadi nilai jam *t* bisa membawa informasi masa depan.
   - Solusi: ERA5 hanya untuk pre-training; kalibrasi akhir dan pengujian hanya dengan PWV GNSS asli.

## Patokan dan jebakan

- Model baru layak dipakai bila mengalahkan **aturan gabungan PWV + persistensi (HSS 0,42)** pada uji silang antarstasiun.
- Pemisahan data harus per waktu dan per stasiun. Split acak membocorkan skor karena data per jam saling berdekatan.
- ML tidak menambah informasi yang tidak ada di data; peningkatan terbesar diperkirakan dari gabungan tren PWV, pola harian, dan hujan terakhir.

## Pengembangan lanjutan lain

- GPT3 untuk ZHD dan Tm di mode live (tanpa ERA5).
- Galileo dan BeiDou lewat RINEX 3 atau stream MSM7.
- Kalibrasi per musim (skor turun dari September ke Oktober).
- Radius layanan dari data pilot dan jawaban "Tadi hujan?".
- Peta jalan proposal: tahun 1 pilot 3–5 stasiun; tahun 2–3 feed ZWD SRGI, radar BMKG, receiver murah di balai desa; tahun 4–6 peringatan banjir kilat untuk BPBD dan WhatsApp resmi; tahun 7–10 densifikasi nasional, asimilasi PWV ke model cuaca, indeks hujan untuk asuransi.

---

Kembali ke [indeks](00_README.md).
