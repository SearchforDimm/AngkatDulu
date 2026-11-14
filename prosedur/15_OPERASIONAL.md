# Operasional: kredensial, pemecahan masalah, dan perintah

## Keamanan dan kredensial

- **Token bot Telegram** dan **akun NTRIP** hanya disimpan di `config\.env` di laptop. Jangan dikirim lewat chat, jangan di-commit.
- Session ID SRGI dan password Earthdata bersifat pribadi. Hapus `download\_netrc.txt` setelah tidak mengunduh dari CDDIS.
- `angkatdulu.db` tidak di-commit (bisa dibangun ulang dengan `db/impor.py`).
- Akun IGS-IP hanya untuk penggunaan pribadi dan kedaluwarsa setelah 6 bulan tidak dipakai. Bila dipakai dalam publikasi, kutip Weber dkk. (2005) sesuai permintaan BKG.

## Pemecahan masalah

| Gejala | Penyebab | Solusi |
|---|---|---|
| `ModuleNotFoundError: No module named 'pandas'` | paket belum terpasang di Python yang dipakai | `python -m pip install -r requirements.txt`; pastikan `python --version` ≥ 3.11 (atau pakai `py -3.11`) |
| BNC `Connection closed` / `Cannot retrieve table` | Ntrip Version `2s` (TLS) dipakai di port 2101, atau proxy terisi | pakai versi `2` di port 2101 (atau `2s` di 443), kosongkan proxy |
| BNC `Unauthorized` | username/password salah, karakter khusus di password, atau akses caster belum aktif | cek email BKG, reset password tanpa karakter khusus, tunggu aktivasi, hubungi `igs-ip@bkg.bund.de` |
| BNC `Not Found` | nama mountpoint salah (0 vs O) atau stream sedang mati | pilih dari **Get table**; coba lagi nanti |
| Tes lewat browser ke caster selalu 403 | browser tidak mengirim akun NTRIP | uji lewat BNC saja |
| Hari tanpa ZTD pagi | hari sebelumnya tidak ada (tanpa jendela 26 jam) | flag `KONVERGENSI` 1 jam pertama, mesin melewatinya |
| Replay lambat di awal | pemanasan 30 hari untuk 4 stasiun | normal (±50 detik) |
| Browser tidak terbuka sendiri | browser bawaan Windows tidak terdeteksi | buka alamat `Dashboard: http://127.0.0.1:...` yang dicetak terminal |
| Port 8000 sudah dipakai | program lain memakai port itu | `demo_bot.py` otomatis memilih port lain dan mencetak alamatnya; atau `--port 8001` |
| Dashboard "Sambungan ke mesin terputus" | `demo_bot.py` berhenti atau terminal ditutup | jalankan lagi; data sesi lama tetap di database |
| Pesan "Gagal dikirim" di panel dashboard | koneksi ke Telegram putus saat itu (sudah dicoba ulang sekali), atau bot diblokir di HP itu | alasan tampil di panel dan di terminal (`! Telegram GAGAL ...`); cek sinyal/hotspot, lalu **Putar ulang** |
| Tidak ada internet di lokasi | bot tidak bisa menghubungi Telegram | `python demo_bot.py --replay --tanpa-bot`: dashboard tetap jalan, pesan tampil di panel |

## Rujukan cepat perintah

```bash
# Laptop: siapkan lingkungan dan jalankan mesin
python -m pip install -r requirements.txt
python db/impor.py
python replay.py --mulai "2026-10-25 05:00" --selesai "2026-10-25 20:00" --stasiun CKRG --cetak
python -m pytest tests
python demo_bot.py --replay              # bot Telegram + dashboard + replay 25 Okt (token di config\.env)
python demo_bot.py --replay --tanpa-bot  # tanpa internet: dashboard saja

# Unduh orbit/jam (laptop)
python pipeline/unduh/unduh_cddis.py --doy 244-306

# Pengolahan GNSS (workspace Linux dengan rnx2rtkp)
python3 pipeline/gnss/jalankan_ppp.py ckrg 244 306 pipeline/gnss/konfig/fix_gr.conf
python3 pipeline/gnss/ekstrak_ztd.py ckrg 244 306

# PWV dan hujan
python3 pipeline/pwv/pwv.py era5_a.grib era5_b.grib data/ztd/ztd_ckrg.csv CKRG
python3 pipeline/hujan/hujan.py CKRG=imerg_ckrg.csv BAKO=imerg_bako.csv CLBG=imerg_clbg.csv CJUR=imerg_cjur.csv

# Kalibrasi dan evaluasi
python pipeline/evaluasi/kalibrasi.py
python pipeline/evaluasi/banding_gabungan.py FOLDER_GABUNG data/evaluasi/banding_gabungan.csv   # lihat 06_KALIBRASI_DAN_HASIL.md
python pipeline/evaluasi/selang_hss.py
```

Konfigurasi PPP per stasiun: CKRG `fix_gr.conf`, BAKO `fix_bako.conf`, CLBG `fix_clbg.conf`, CJUR `fix_cjur_a.conf` (DOY 244–266) dan `fix_cjur_b.conf` (DOY 267 ke atas). Varian `_g` = GPS saja, `_g30` / `_gr30` = simulasi langit terhalang.

---

Kembali ke [indeks](00_README.md).
