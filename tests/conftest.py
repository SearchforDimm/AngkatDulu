import sys
from pathlib import Path

import pytest

AKAR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(AKAR))
sys.path.insert(0, str(AKAR / 'db'))
sys.path.insert(0, str(AKAR / 'pipeline' / 'evaluasi'))


@pytest.fixture(scope='session')
def db(tmp_path_factory):
    from impor import bangun
    con, aturan, aid = bangun(tmp_path_factory.mktemp('db') / 'uji.db', aturan=AKAR / 'config' / 'aturan.yaml')
    return con, aturan, aid


@pytest.fixture(scope='session')
def folder_data(tmp_path_factory):
    """Folder datar berisi pwv_30menit_*.csv, hujan_30menit.csv, awal_hujan.csv (masukan kalibrasi)."""
    d = tmp_path_factory.mktemp('data')
    for f in list((AKAR / 'data' / 'pwv').glob('pwv_30menit_*.csv')) + list((AKAR / 'data' / 'hujan').glob('*.csv')):
        (d / f.name).write_bytes(f.read_bytes())
    return d
