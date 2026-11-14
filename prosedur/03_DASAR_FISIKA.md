# Dasar fisika: dari sinyal satelit ke PWV

1. **ZTD dari PPP.** RTKLIB menaksir ZTD bersama jam receiver dan ambiguitas fase, tiap 30 detik, dengan koordinat stasiun ditetapkan.
2. **ZHD dari tekanan** (Saastamoinen):

   ```
   ZHD [m] = 0,0022768 · P [hPa] / (1 − 0,00266 · cos 2φ − 0,00028 · h_elipsoid [km])
   ```

3. **ZWD** = ZTD − ZHD.
4. **Tm dari suhu permukaan** (Bevis): `Tm = 70,2 + 0,72 · Ts` (K).
5. **Faktor konversi**:

   ```
   Π = 10⁶ / (ρw · Rv · (k3 / Tm + k2′))
   ρw = 1000 kg/m³, Rv = 461,5 J/(kg·K), k2′ = 22,1 K/hPa, k3 = 3,739·10⁵ K²/hPa
   ```

6. **PWV** = Π · ZWD (dalam mm). Rata-rata Π di data kita 0,164.

Kepekaan penting:

- 1 mm ZTD ≈ 0,16 mm PWV.
- 1 hPa galat tekanan ≈ 2,3 mm ZHD ≈ 0,37 mm PWV. Karena itu tekanan stasiun dihitung hati-hati (langkah ZTD → PWV di [05_ALUR_PENGOLAHAN.md](05_ALUR_PENGOLAHAN.md)).
- Uji dengan tekanan dan suhu konstan hanya menggeser PWV 0,64 mm (RMS), jadi untuk mode live model empiris (GPT3 atau rata-rata ERA5 per stasiun) cukup.

---

Kembali ke [indeks](00_README.md).
