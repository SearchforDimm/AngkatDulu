"""Sisipkan header GLONASS SLOT/FRQ # (FCN berlaku untuk semua stasiun) ke RINEX 2.11."""
import sys, os, glob
FCN = [' 24 R01  1 R02 -4 R03  5 R04  6 R05  1 R06 -4 R07  5 R08  6 GLONASS SLOT / FRQ #',
       '    R09 -2 R10 -7 R11  0 R12 -1 R13 -2 R14 -7 R15  0 R16 -1 GLONASS SLOT / FRQ #',
       '    R17  4 R18 -3 R19  3 R20  2 R21  4 R22 -3 R23  3 R24  2 GLONASS SLOT / FRQ #']
src, dst = sys.argv[1], sys.argv[2]; os.makedirs(dst, exist_ok=True)
for f in sorted(glob.glob(os.path.join(src, '*.26o'))):
    out = os.path.join(dst, os.path.basename(f).replace('.26o', '_dengan_fcn.26o'))
    if os.path.exists(out): continue
    lines = open(f, errors='ignore').read().split('\n')
    k = next(i for i, l in enumerate(lines) if 'END OF HEADER' in l)
    lines = [l for l in lines[:k] if 'GLONASS SLOT' not in l] + [l.ljust(60) if False else l for l in FCN] + lines[k:]
    open(out, 'w').write('\n'.join(lines))
    nav = f[:-1] + 'n'
    if os.path.exists(nav): os.system(f'cp "{nav}" "{dst}/"')
print('selesai', dst)
