-- AngkatDulu · skema database prototipe (SQLite 3.35+)
-- Dibangun oleh db/impor.py. Versi skema: 1.1 (status_stasiun.persentil ditambahkan, 5 Nov 2026).
-- Konvensi: nama tabel/kolom bahasa Indonesia snake_case; waktu TEXT ISO 8601 UTC berakhiran Z;
-- enum memakai CHECK; semua waktu di mode replay adalah waktu simulasi (waktu data).
PRAGMA foreign_keys = ON;

-- ============ Referensi ============
CREATE TABLE stasiun (
  kode                 TEXT PRIMARY KEY CHECK (length(kode) = 4 AND kode = upper(kode)),
  nama                 TEXT NOT NULL,
  lat                  REAL NOT NULL CHECK (lat BETWEEN -11.5 AND 6.5),
  lon                  REAL NOT NULL CHECK (lon BETWEEN 94.0 AND 141.5),
  tinggi_elipsoid_m    REAL,
  tinggi_ortometrik_m  REAL,
  status               TEXT NOT NULL DEFAULT 'SEHAT' CHECK (status IN ('SEHAT','GANGGUAN','MATI')),
  diperbarui_utc       TEXT NOT NULL
);

CREATE TABLE run_pengolahan (
  id                TEXT PRIMARY KEY,                       -- mis. ppp-20261102-0930
  jenis             TEXT NOT NULL CHECK (jenis IN ('PPP','PWV','HUJAN','AWAL_HUJAN','EVALUASI','IMPOR')),
  versi_perangkat   TEXT,                                   -- mis. RTKLIB-EX 2.5.1
  konfigurasi       TEXT,                                   -- nama file conf + hash
  periode_mulai     TEXT,
  periode_selesai   TEXT,
  dimulai_utc       TEXT NOT NULL,
  selesai_utc       TEXT,
  catatan           TEXT
);

-- ============ Observasi (hasil pemrosesan) ============
CREATE TABLE observasi_pwv (
  kode_stasiun   TEXT NOT NULL REFERENCES stasiun(kode),
  waktu_utc      TEXT NOT NULL,                             -- awal slot 30 menit
  run_id         TEXT NOT NULL REFERENCES run_pengolahan(id),
  pwv_mm         REAL NOT NULL CHECK (pwv_mm BETWEEN 0 AND 100),
  sigma_pwv_mm   REAL,
  ztd_m          REAL, zhd_m REAL, zwd_m REAL,
  tekanan_hpa    REAL, suhu_k REAL, tm_k REAL,
  n_epoch        INTEGER CHECK (n_epoch BETWEEN 0 AND 60),
  sumber_meteo   TEXT NOT NULL CHECK (sumber_meteo IN ('ERA5','ERA5_ISI','GPT3','SENSOR')),
  produk_orbit   TEXT NOT NULL CHECK (produk_orbit IN ('MGEX_FINAL','RAPID','SSR_REALTIME','FEED_SRGI')),
  flag_kualitas  TEXT NOT NULL CHECK (flag_kualitas IN ('OK','KONVERGENSI','CELAH','METEO_ISI','ORBIT_RAPID')),
  PRIMARY KEY (kode_stasiun, waktu_utc, run_id)
);

CREATE TABLE observasi_hujan (
  kode_stasiun      TEXT NOT NULL REFERENCES stasiun(kode),
  waktu_utc         TEXT NOT NULL,
  sumber            TEXT NOT NULL CHECK (sumber IN ('IMERG_LATE_V07','IMERG_FINAL_V07','PENAKAR')),
  jarak_km          REAL NOT NULL DEFAULT 0,                -- 0 = sel di atas stasiun; 10/25/50 untuk uji radius
  hujan_mm_per_jam  REAL CHECK (hujan_mm_per_jam IS NULL OR hujan_mm_per_jam >= 0),
  run_id            TEXT REFERENCES run_pengolahan(id),
  PRIMARY KEY (kode_stasiun, waktu_utc, sumber, jarak_km)
);

CREATE TABLE awal_hujan (
  id                INTEGER PRIMARY KEY,
  kode_stasiun      TEXT NOT NULL REFERENCES stasiun(kode),
  waktu_utc         TEXT NOT NULL,
  hujan_mm_per_jam  REAL NOT NULL,
  sumber            TEXT NOT NULL CHECK (sumber IN ('IMERG','LAPORAN_WARGA')),
  definisi          TEXT NOT NULL,                          -- mis. ">=1 mm/jam setelah >=3 jam <0,2"
  run_id            TEXT REFERENCES run_pengolahan(id),
  UNIQUE (kode_stasiun, waktu_utc, sumber)
);

-- ============ Aturan dan evaluasi ============
CREATE TABLE aturan (
  id                  INTEGER PRIMARY KEY,
  nama                TEXT NOT NULL,
  versi               TEXT NOT NULL,
  parameter_json      TEXT NOT NULL CHECK (json_valid(parameter_json)),
  periode_kalibrasi   TEXT,
  dibuat_utc          TEXT NOT NULL,
  UNIQUE (nama, versi)
);

CREATE TABLE aturan_stasiun (
  kode_stasiun    TEXT NOT NULL REFERENCES stasiun(kode),
  aturan_id       INTEGER NOT NULL REFERENCES aturan(id),
  berlaku_mulai   TEXT NOT NULL,
  berlaku_sampai  TEXT,
  PRIMARY KEY (kode_stasiun, berlaku_mulai),
  CHECK (berlaku_sampai IS NULL OR berlaku_sampai > berlaku_mulai)
);

CREATE TABLE metrik_evaluasi (
  id                        INTEGER PRIMARY KEY,
  run_id                    TEXT NOT NULL REFERENCES run_pengolahan(id),
  aturan_id                 INTEGER REFERENCES aturan(id),   -- NULL untuk baseline
  nama_aturan               TEXT NOT NULL,
  kode_evaluasi             TEXT NOT NULL CHECK (kode_evaluasi IN ('S-45','P-3J','E-3J')),
  kode_stasiun              TEXT NOT NULL REFERENCES stasiun(kode),
  jenis_periode             TEXT NOT NULL CHECK (jenis_periode IN ('KALIBRASI','UJI','IN_SAMPLE')),
  periode_mulai             TEXT NOT NULL,
  periode_selesai           TEXT NOT NULL,
  hit INTEGER, alarm_palsu INTEGER, terlewat INTEGER, benar_negatif INTEGER,
  waktu_menyala             REAL,
  pod REAL, far REAL, csi REAL, hss REAL,
  n_awal_hujan              INTEGER,
  awal_hujan_diperingatkan  INTEGER,
  lead_time_median_menit    REAL
);

-- ============ Runtime mesin ============
CREATE TABLE sesi_replay (
  id               INTEGER PRIMARY KEY,
  nama             TEXT NOT NULL,
  mode             TEXT NOT NULL CHECK (mode IN ('REPLAY','LIVE')),
  periode_mulai    TEXT,                                    -- waktu data (replay)
  periode_selesai  TEXT,
  detik_per_tick   REAL,                                    -- kecepatan replay
  waktu_simulasi   TEXT,                                    -- posisi jam saat ini
  status           TEXT NOT NULL CHECK (status IN ('BERJALAN','JEDA','SELESAI')),
  dimulai_nyata    TEXT NOT NULL
);

CREATE TABLE status_stasiun (
  sesi_id         INTEGER NOT NULL REFERENCES sesi_replay(id),
  kode_stasiun    TEXT NOT NULL REFERENCES stasiun(kode),
  waktu_utc       TEXT NOT NULL,
  aturan_id       INTEGER NOT NULL REFERENCES aturan(id),
  pwv_1jam_mm     REAL,
  anomali_mm      REAL,
  persentil       REAL,                                     -- peringkat PWV 1 jam terhadap 15 hari terakhir (0–100)
  delta_3jam_mm   REAL,
  level           TEXT NOT NULL CHECK (level IN ('AMAN','WASPADA','BERPOTENSI','TANPA_DATA')),
  PRIMARY KEY (sesi_id, kode_stasiun, waktu_utc)
);

CREATE TABLE peringatan (
  id              INTEGER PRIMARY KEY,
  sesi_id         INTEGER NOT NULL REFERENCES sesi_replay(id),
  kode_stasiun    TEXT NOT NULL REFERENCES stasiun(kode),
  aturan_id       INTEGER NOT NULL REFERENCES aturan(id),
  level           TEXT NOT NULL CHECK (level IN ('WASPADA','BERPOTENSI')),
  mulai_utc       TEXT NOT NULL,
  selesai_utc     TEXT,
  pwv_pemicu_mm   REAL,
  diikuti_hujan   INTEGER CHECK (diikuti_hujan IN (0,1)),  -- diisi evaluator: hujan IMERG dalam 3 jam
  CHECK (selesai_utc IS NULL OR selesai_utc > mulai_utc)
);

-- ============ Pengguna dan pesan ============
CREATE TABLE pengguna (
  id                 INTEGER PRIMARY KEY,
  telegram_chat_id   INTEGER NOT NULL UNIQUE,
  jenis_chat         TEXT NOT NULL CHECK (jenis_chat IN ('PRIBADI','GRUP')),
  nama_tampilan      TEXT,
  peran              TEXT CHECK (peran IN ('PETANI','PENYULUH','KELOMPOK_TANI','TIM','LAINNYA')),
  kepekaan           TEXT NOT NULL DEFAULT 'PEKA' CHECK (kepekaan IN ('PEKA','HEMAT')),
  pengguna_uji       INTEGER NOT NULL DEFAULT 0 CHECK (pengguna_uji IN (0,1)),
  aktif              INTEGER NOT NULL DEFAULT 1 CHECK (aktif IN (0,1)),
  bergabung_utc      TEXT NOT NULL,
  berhenti_utc       TEXT
);

CREATE TABLE lokasi_pengguna (
  id             INTEGER PRIMARY KEY,
  pengguna_id    INTEGER NOT NULL REFERENCES pengguna(id) ON DELETE CASCADE,
  lat            REAL NOT NULL,                             -- dibulatkan 3 desimal (±100 m)
  lon            REAL NOT NULL,
  kode_stasiun   TEXT NOT NULL REFERENCES stasiun(kode),
  jarak_km       REAL NOT NULL CHECK (jarak_km >= 0),
  aktif          INTEGER NOT NULL DEFAULT 1 CHECK (aktif IN (0,1)),
  dibuat_utc     TEXT NOT NULL
);

CREATE TABLE pesan (
  id                    INTEGER PRIMARY KEY,
  pengguna_id           INTEGER NOT NULL REFERENCES pengguna(id) ON DELETE CASCADE,
  sesi_id               INTEGER REFERENCES sesi_replay(id),
  peringatan_id         INTEGER REFERENCES peringatan(id),
  jenis                 TEXT NOT NULL CHECK (jenis IN ('SAMBUTAN','INFO_JARAK','KONDISI_AWAL','STATUS',
                              'RINGKASAN_PAGI','BERPOTENSI','AMAN_LAGI','TANYA_HUJAN','TERIMA_LAPORAN')),
  sebagai_notifikasi    INTEGER NOT NULL DEFAULT 1 CHECK (sebagai_notifikasi IN (0,1)),
  isi                   TEXT NOT NULL,
  dijadwalkan_utc       TEXT NOT NULL,                      -- waktu simulasi di mode replay
  terkirim_utc          TEXT,                               -- waktu simulasi saat terkirim
  terkirim_nyata        TEXT,                               -- jam dinding
  status                TEXT NOT NULL CHECK (status IN ('DIJADWALKAN','DITAHAN','TERKIRIM','GAGAL','DIBATALKAN')),
  alasan                TEXT,                               -- mis. KUOTA_HARIAN, DI_LUAR_JAM
  telegram_message_id   INTEGER
);

CREATE TABLE umpan_balik (
  id              INTEGER PRIMARY KEY,
  pengguna_id     INTEGER NOT NULL REFERENCES pengguna(id) ON DELETE CASCADE,
  pesan_id        INTEGER REFERENCES pesan(id),             -- pesan TANYA_HUJAN yang dijawab
  peringatan_id   INTEGER REFERENCES peringatan(id),
  jenis           TEXT NOT NULL CHECK (jenis IN ('JAWABAN_TADI_HUJAN','LAPOR_HUJAN')),
  nilai           TEXT CHECK (nilai IN ('YA','TIDAK')),
  waktu_utc       TEXT NOT NULL,
  lat REAL, lon REAL,
  CHECK (jenis = 'LAPOR_HUJAN' OR nilai IS NOT NULL)
);

-- ============ Indeks ============
CREATE INDEX ix_pwv_stasiun_waktu    ON observasi_pwv(kode_stasiun, waktu_utc);
CREATE INDEX ix_hujan_stasiun_waktu  ON observasi_hujan(kode_stasiun, waktu_utc);
CREATE INDEX ix_status_stasiun_waktu ON status_stasiun(kode_stasiun, waktu_utc);
CREATE INDEX ix_peringatan_stasiun   ON peringatan(kode_stasiun, mulai_utc);
CREATE UNIQUE INDEX ux_peringatan_terbuka ON peringatan(sesi_id, kode_stasiun) WHERE selesai_utc IS NULL;
CREATE UNIQUE INDEX ux_lokasi_aktif  ON lokasi_pengguna(pengguna_id) WHERE aktif = 1;
CREATE INDEX ix_lokasi_stasiun       ON lokasi_pengguna(kode_stasiun) WHERE aktif = 1;
CREATE INDEX ix_pesan_pengguna_waktu ON pesan(pengguna_id, dijadwalkan_utc);
CREATE INDEX ix_pesan_jatuh_tempo    ON pesan(status, dijadwalkan_utc);
CREATE INDEX ix_umpan_peringatan     ON umpan_balik(peringatan_id);

-- ============ View ============
-- PWV dari run terbaru untuk tiap slot (mis. run ulang dengan orbit final menggantikan rapid)
CREATE VIEW v_pwv_aktif AS
SELECT kode_stasiun, waktu_utc, pwv_mm, sigma_pwv_mm, flag_kualitas, sumber_meteo, produk_orbit, run_id
FROM (
  SELECT o.*, ROW_NUMBER() OVER (PARTITION BY o.kode_stasiun, o.waktu_utc
                                 ORDER BY r.dimulai_utc DESC) AS urut
  FROM observasi_pwv o JOIN run_pengolahan r ON r.id = o.run_id
) WHERE urut = 1;

-- Pelanggan aktif per stasiun
CREATE VIEW v_pelanggan_stasiun AS
SELECT l.kode_stasiun, p.id AS pengguna_id, p.telegram_chat_id, p.kepekaan, l.jarak_km
FROM lokasi_pengguna l JOIN pengguna p ON p.id = l.pengguna_id
WHERE l.aktif = 1 AND p.aktif = 1;

-- Jumlah notifikasi push per pengguna per tanggal WIB (untuk kuota 2/hari)
CREATE VIEW v_notifikasi_harian AS
SELECT pengguna_id, sesi_id,
       date(datetime(terkirim_utc, '+7 hours')) AS tanggal_wib,
       COUNT(*) AS jumlah
FROM pesan
WHERE status = 'TERKIRIM' AND sebagai_notifikasi = 1
GROUP BY pengguna_id, sesi_id, tanggal_wib;

-- Rekam jejak "x dari n peringatan BERPOTENSI diikuti hujan" per stasiun
CREATE VIEW v_rekam_jejak AS
SELECT sesi_id, kode_stasiun,
       COUNT(*)                         AS n_peringatan,
       SUM(COALESCE(diikuti_hujan, 0))  AS n_diikuti_hujan
FROM peringatan
WHERE level = 'BERPOTENSI' AND diikuti_hujan IS NOT NULL
GROUP BY sesi_id, kode_stasiun;
