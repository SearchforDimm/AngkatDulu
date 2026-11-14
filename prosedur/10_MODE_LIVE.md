# Mode live: status dan rencana

## Yang dibutuhkan

PPP real-time butuh dua aliran sekaligus:

1. **Pengamatan stasiun** (RTCM 3 MSM) termasuk ephemeris siar.
2. **Koreksi orbit dan jam satelit** (SSR), pengganti SP3/CLK.

Lalu: `rtkrcv` (atau BNC) → ZTD per epoch → PWV (tekanan dan Tm dari rata-rata ERA5 per stasiun atau GPT3) → slot 30 menit → `LiveSource` (antarmuka sama dengan `ReplaySource`) → mesin yang sama → bot.

## Temuan dan status per 13 Nov

| Hal | Status |
|---|---|
| Stream dedicated BIG (RTCM 3 MSM5, `36.95.202.211:2023`) | **Tidak tersedia**: server BIG bermasalah. Panitia akan mengirim PWV 4 stasiun lewat email untuk DOY yang diminta. |
| PPP hanya dengan ephemeris siar (tanpa koreksi) | **Tidak layak**: uji 2 bulan 4 stasiun, simpangan ZTD 55–85 mm (±9–14 mm PWV), korelasi per jam ±0,5 (CJUR 0,1). |
| Akun IGS-IP (BKG) | Aktif untuk `igs-ip.net`, `products.igs-ip.net`, `euref-ip.net` (port 2101, atau 443 dengan TLS). |
| Stream pengamatan BAKO | `BAKO00IDN0` di `igs-ip.net`: RTCM 3.3 MSM7 1 detik, GPS+GLONASS+Galileo+BeiDou+QZSS, ephemeris ikut (1019/1020/1042/1044/1045/1046), diteruskan dari Geoscience Australia. Uji BNC 13 Nov 19.45: login diterima, tetapi mountpoint dibalas `Not Found` walau dipilih dari source table. Kemungkinan besar relay dari Geoscience Australia sedang mati. Di portal GA (`portal.ga.gov.au`), stasiun di kompleks BIG Cibinong yang terdaftar adalah **CIBG** (DOMES 23101M005, −6,49036; 106,84917), statusnya **No stream**; BAKO sendiri ber-DOMES 23101M002. Jalur cadangan: akun Geoscience Australia (`gnss.ga.gov.au/registration`, lalu minta izin stream ke `gnss@ga.gov.au`), sambung langsung ke `ntrip.data.gnss.ga.gov.au`, port `443`, Ntrip Version `2s`, mountpoint `BAKO00IDN0`. |
| Koreksi SSR | Utama `SSRA00CNE0` (CNES, RTCM-SSR, orbit+jam+bias kode+bias fase, G/R/E/C, 5 detik). Cadangan `SSRA03IGS1` (gabungan IGS, IGS-SSR, tanpa bias kode, 10 detik). Pilih **SSRA** (acuan pusat fase antena), bukan SSRC; abaikan akhiran `_SIRGAS2000`. Semua pesan bisa dibaca RTKLIB-EX. Uji BNC 13 Nov 19.45: **`SSRA00CNE0` berhasil diterima** (±47 kB dalam beberapa menit). |
| CKRG, CLBG, CJUR live | Hanya lewat server BIG → mode replay + PWV kiriman BIG. Karena koreksi SSR sudah jalan, begitu stream dedicated BIG pulih, keempat stasiun bisa langsung diolah live. |

## Pengaturan BNC (uji koneksi di laptop)

1. Tab **Network**: Proxy host/port **dikosongkan**.
2. **Add Stream → Caster**: host `igs-ip.net` / `products.igs-ip.net`, port `2101`, **Ntrip Version `2`** (`2s` hanya untuk port 443), user dan password akun BKG.
3. **Get table**, pilih mountpoint dari daftar (jangan diketik), **Select**, lalu **Start**.
4. Berhasil bila kolom **bytes** terus bertambah.

## Rencana demo

- **BAKO live** (bila kedua stream jalan), **CKRG/CLBG/CJUR replay** + PWV BIG sebagai pembanding.
- **Cadangan**: dashboard menampilkan stream yang masuk (jumlah satelit per sistem), peringatan berjalan dalam mode replay.
- Sebelum dipakai, ZTD real-time dibandingkan dengan hasil olahan produk final beberapa hari untuk mengukur selisih tetap sebelum digabung dengan riwayat 15 hari.

Rencana jangka panjang (ML dan lainnya) ada di [11_RENCANA_ML.md](11_RENCANA_ML.md).

---

Kembali ke [indeks](00_README.md).
