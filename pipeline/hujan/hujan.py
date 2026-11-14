"""IMERG 30 menit -> hujan_30menit.csv dan awal_hujan.csv (kontrak data AngkatDulu).

python3 hujan.py KODE=file_imerg.csv [KODE=file_imerg.csv ...]

Awal hujan = slot pertama >= 0,2 mm/jam setelah >= 3 jam (6 slot) berturut-turut < 0,2 mm/jam,
dan kejadian itu (sampai 3 jam kering lagi) punya puncak >= 1 mm/jam.
Slot IMERG yang hilang dianggap tidak diketahui: tidak dihitung sebagai kering.
"""
import sys
import numpy as np, pandas as pd

BASAH, PUNCAK, KERING_SLOT = 0.2, 1.0, 6
DEFINISI = 'slot pertama >=0,2 mm/jam setelah >=3 jam <0,2; puncak kejadian >=1 mm/jam'


def baca_imerg(path):
    baris = open(path).read().splitlines()
    k = next(i for i, l in enumerate(baris) if l.startswith('time'))
    d = pd.read_csv(path, skiprows=k + 1, names=['t', 'mm'])
    d['t'] = pd.to_datetime(d.t, format='%Y-%m-%d %H:%M:%S')
    s = d.set_index('t').mm.astype(float)
    s[s < -9000] = np.nan
    return s.asfreq('30min')


def awal_hujan(r):
    v = r.to_numpy(); hasil = []; kering = 0
    for i, x in enumerate(v):
        if np.isnan(x):
            kering = 0
            continue
        if x >= BASAH:
            if kering >= KERING_SLOT:
                j, k2, pk = i, 0, 0.0
                while j < len(v) and k2 < KERING_SLOT:
                    y = 0.0 if np.isnan(v[j]) else v[j]
                    pk = max(pk, y); k2 = k2 + 1 if y < BASAH else 0; j += 1
                if pk >= PUNCAK:
                    hasil.append((r.index[i], x, pk))
            kering = 0
        else:
            kering += 1
    return pd.DataFrame(hasil, columns=['waktu', 'hujan_mm_per_jam', 'puncak_mm_per_jam'])


def main():
    hujan, awal = [], []
    for arg in sys.argv[1:]:
        kode, path = arg.split('=', 1)
        r = baca_imerg(path)
        h = pd.DataFrame({'waktu_utc': r.index.strftime('%Y-%m-%dT%H:%M:%SZ'), 'kode_stasiun': kode,
                          'hujan_mm_per_jam': r.round(2).to_numpy(), 'sumber': 'IMERG_LATE_V07'})
        hujan.append(h)
        a = awal_hujan(r)
        a.insert(0, 'kode_stasiun', kode)
        a['jam_wib'] = (a.waktu + pd.Timedelta(hours=7)).dt.strftime('%Y-%m-%d %H:%M')
        a['waktu_utc'] = a.pop('waktu').dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        a['sumber'], a['definisi'] = 'IMERG', DEFINISI
        awal.append(a)
        jam = (pd.to_datetime(a.jam_wib)).dt.hour
        print(f'{kode}: {len(a)} awal hujan, {int(((jam >= 6) & (jam < 18)).sum())} di jam 06–18 WIB')
    pd.concat(hujan).to_csv('hujan_30menit.csv', index=False)
    kolom = ['kode_stasiun', 'waktu_utc', 'jam_wib', 'hujan_mm_per_jam', 'puncak_mm_per_jam', 'sumber', 'definisi']
    pd.concat(awal)[kolom].round(2).to_csv('awal_hujan.csv', index=False)


if __name__ == '__main__':
    main()
