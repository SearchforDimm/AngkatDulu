"""PPP-fixed GPS+GLONASS per hari dengan jendela 26 jam (mulai 22.00 UTC hari sebelumnya).

Untuk hari D: epoch hari D-1 pukul 22.00–24.00 UTC digabung di depan RINEX hari D, lalu diolah
dengan SP3/CLK kedua hari. ZTD yang disimpan hanya 00.00–24.00 UTC hari D, sehingga masa
konvergensi jatuh di hari sebelumnya dan tidak ada celah pukul 07.00–08.00 WIB.
Bila hari D-1 tidak ada, hari D diolah sendiri dan 1 jam pertama ditandai KONVERGENSI.

python3 jalankan_ppp.py STASIUN DOY_AWAL DOY_AKHIR KONFIG
"""
import glob, math, os, re, subprocess, sys
import pandas as pd

RNX = '/home/claude/rtklibexplorer/rtklib/app/consapp/rnx2rtkp/gcc/rnx2rtkp'
EPOCH = re.compile(r'^ (\d\d) ([ \d]\d) ([ \d]\d) ([ \d]\d) ([ \d]\d) ([ \d]\d\.\d{7})  ([0-6])([ \d]{3})')


def tipe_obs(header):
    baris = [l for l in header if '# / TYPES OF OBSERV' in l]
    n = int(baris[0][:6])
    tipe = []
    for l in baris:
        tipe += l[6:60].split()
    return tipe[:n]


def ubah_tipe(blok, dari, ke):
    """Susun ulang nilai observasi dari urutan tipe 'dari' ke urutan tipe 'ke' (RINEX 2.11)."""
    m = EPOCH.match(blok[0])
    if int(m.group(7)) > 1:
        return blok
    n = int(m.group(8)); kepala = 1 + (math.ceil(n / 12) - 1)
    bps_dari, bps_ke = math.ceil(len(dari) / 5), math.ceil(len(ke) / 5)
    hasil = blok[:kepala]
    for j in range(n):
        baris = blok[kepala + j * bps_dari: kepala + (j + 1) * bps_dari]
        nilai = {}
        for b, l in enumerate(baris):
            l = l.ljust(80)
            for c in range(5):
                i = b * 5 + c
                if i < len(dari):
                    nilai[dari[i]] = l[16 * c:16 * c + 16]
        isi = [nilai.get(t, ' ' * 16) for t in ke]
        for b in range(bps_ke):
            hasil.append(''.join(isi[b * 5:b * 5 + 5]).rstrip())
    return hasil


def baca(path):
    teks = open(path, errors='ignore').read().split('\n')
    k = next(i for i, l in enumerate(teks) if 'END OF HEADER' in l)
    header, badan = teks[:k + 1], teks[k + 1:]
    ntipe = len(tipe_obs(header))
    baris_per_sat = math.ceil(ntipe / 5)
    rekaman, i = [], 0
    while i < len(badan):
        m = EPOCH.match(badan[i])
        if not m:
            i += 1
            continue
        flag, n = int(m.group(7)), int(m.group(8))
        if flag <= 1 or flag == 6:
            panjang = 1 + (math.ceil(n / 12) - 1) + n * baris_per_sat
        else:
            panjang = 1 + n
        jam = int(m.group(4)) + int(m.group(5)) / 60 + float(m.group(6)) / 3600
        rekaman.append((jam, badan[i:i + panjang]))
        i += panjang
    return header, rekaman


def gabung(prev, cur, out, mulai_jam=22.0):
    h_prev, rek_prev = baca(prev)
    header, rek_cur = baca(cur)
    t_prev, t_cur = tipe_obs(h_prev), tipe_obs(header)
    header = [l for l in header if 'TIME OF FIRST OBS' not in l]
    with open(out, 'w') as f:
        f.write('\n'.join(header) + '\n')
        for jam, blok in rek_prev:
            if jam >= mulai_jam:
                if t_prev != t_cur:
                    blok = ubah_tipe(blok, t_prev, t_cur)
                f.write('\n'.join(blok) + '\n')
        for _, blok in rek_cur:
            f.write('\n'.join(blok) + '\n')


def produk(doy):
    for pre in ('COD0MGXFIN', 'COD0OPSFIN', 'COD0OPSRAP'):
        sp = f'prod/{pre}_2026{doy:03d}0000_01D_05M_ORB.SP3'
        ck = f'prod/{pre}_2026{doy:03d}0000_01D_30S_CLK.CLK'
        if os.path.exists(sp) and os.path.exists(ck):
            return pre, sp, ck
    return None, None, None


def main():
    st, d0, d1, conf = sys.argv[1].lower(), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    obsdir = f'obs_{st}'
    os.makedirs('out26', exist_ok=True); os.makedirs('tmp', exist_ok=True)
    ringkas = []
    for d in range(d0, d1 + 1):
        cur = f'{obsdir}/{st}{d:03d}0_dengan_fcn.26o'
        nav = f'{obsdir}/{st}{d:03d}0.26n'
        pre, sp, ck = produk(d)
        if not os.path.exists(cur) or pre is None:
            ringkas.append(dict(doy=d, status='LEWAT', alasan='rinex' if not os.path.exists(cur) else 'produk'))
            continue
        prev = f'{obsdir}/{st}{d - 1:03d}0_dengan_fcn.26o'
        ppre, psp, pck = produk(d - 1)
        jendela = os.path.exists(prev) and ppre is not None
        inp = cur
        args = [RNX, '-k', conf, '-o', f'out26/{st}{d:03d}.pos']
        files = [cur, nav, sp, ck]
        if jendela:
            inp = f'tmp/{st}{d:03d}_26j.26o'
            gabung(prev, cur, inp)
            pnav = f'{obsdir}/{st}{d - 1:03d}0.26n'
            files = [inp, nav] + ([pnav] if os.path.exists(pnav) else []) + [psp, pck, sp, ck]
        subprocess.run(args + files, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        ringkas.append(dict(doy=d, status='OK', jendela_26j=jendela, produk=pre))
        if jendela:
            os.remove(inp)
    print(pd.DataFrame(ringkas).to_string(index=False))


if __name__ == '__main__':
    main()
