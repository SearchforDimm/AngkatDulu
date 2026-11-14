"""Pembaca GRIB1 minimal (simple packing) untuk ERA5 single levels."""
import struct, numpy as np

def ibm2float(b):
    s = -1 if b[0] & 0x80 else 1
    e = (b[0] & 0x7f) - 64
    m = int.from_bytes(b[1:4], 'big') / 16777216.0
    return s * m * 16 ** e

def s16(b):
    v = int.from_bytes(b, 'big')
    return -(v & 0x7fff) if v & 0x8000 else v

def read(path):
    d = open(path, 'rb').read()
    pos, out = 0, []
    while True:
        i = d.find(b'GRIB', pos)
        if i < 0: break
        L = int.from_bytes(d[i+4:i+7], 'big')
        p = i + 8
        pl = int.from_bytes(d[p:p+3], 'big'); pds = d[p:p+pl]
        param = pds[8]; flag = pds[7]
        yy, mm, dd, hh, mi = pds[12], pds[13], pds[14], pds[15], pds[16]
        cent = pds[24]; year = (cent - 1) * 100 + yy
        D = s16(pds[26:28])
        q = p + pl
        gl = 0
        if flag & 0x80:
            gl = int.from_bytes(d[q:q+3], 'big'); gds = d[q:q+gl]
            ni = int.from_bytes(gds[6:8], 'big'); nj = int.from_bytes(gds[8:10], 'big')
            def sl(b):
                v = int.from_bytes(b, 'big'); return -(v & 0x7fffff) if v & 0x800000 else v
            la1, lo1 = sl(gds[10:13]) / 1000, sl(gds[13:16]) / 1000
            la2, lo2 = sl(gds[17:20]) / 1000, sl(gds[20:23]) / 1000
        q += gl
        if flag & 0x40:
            q += int.from_bytes(d[q:q+3], 'big')
        bl = int.from_bytes(d[q:q+3], 'big'); bds = d[q:q+bl]
        E = s16(bds[4:6]); R = ibm2float(bds[6:10]); nb = bds[10]
        npts = ni * nj
        bits = np.unpackbits(np.frombuffer(bds[11:], np.uint8))[:npts * nb].reshape(npts, nb)
        ints = bits.dot(1 << np.arange(nb - 1, -1, -1))
        vals = (R + ints * 2.0 ** E) / 10 ** D
        out.append(dict(param=param, time=f'{year:04d}-{mm:02d}-{dd:02d} {hh:02d}:{mi:02d}',
                        lats=np.linspace(la1, la2, nj), lons=np.linspace(lo1, lo2, ni),
                        vals=vals.reshape(nj, ni)))
        pos = i + L
    return out
