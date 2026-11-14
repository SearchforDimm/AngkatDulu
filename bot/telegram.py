"""Klien Telegram Bot API yang tipis (HTTPS + long polling), tanpa pustaka bot pihak ketiga.

Hanya memanggil metode yang dipakai AngkatDulu. Token tidak pernah dicetak.
"""
import json
from pathlib import Path

import requests


class GalatTelegram(RuntimeError):
    pass


def baca_token(path_env):
    """Baca TELEGRAM_BOT_TOKEN dari file .env sederhana (KUNCI=nilai per baris)."""
    p = Path(path_env)
    if not p.exists():
        raise GalatTelegram(f'File {p} tidak ditemukan. Salin config/env_contoh.txt menjadi config/.env lalu isi token.')
    for baris in p.read_text(encoding='utf-8-sig').splitlines():
        baris = baris.strip()
        if baris.startswith('#') or '=' not in baris:
            continue
        kunci, nilai = baris.split('=', 1)
        if kunci.strip() == 'TELEGRAM_BOT_TOKEN':
            nilai = nilai.strip().strip('"').strip("'")
            if nilai:
                return nilai
    raise GalatTelegram(f'TELEGRAM_BOT_TOKEN kosong di {p}.')


class Telegram:
    def __init__(self, token, sesi=None, alamat='https://api.telegram.org'):
        self._url = f'{alamat}/bot{token}/'
        self._sesi = sesi or requests.Session()

    def panggil(self, metode, batas_detik=10, **param):
        """Satu panggilan Bot API. Telegram biasanya menjawab < 1 detik, jadi batas baca 10 detik (sambung 5 detik)
        supaya replay tidak tertahan lama saat jaringan tersendat; long polling menambah waktu tunggunya sendiri."""
        data = {k: (json.dumps(v) if isinstance(v, (dict, list)) else v) for k, v in param.items() if v is not None}
        try:
            r = self._sesi.post(self._url + metode, data=data, timeout=(5, batas_detik))
        except requests.RequestException as e:          # pesan galat tanpa URL (URL memuat token)
            raise GalatTelegram(f'{metode}: koneksi gagal ({type(e).__name__})') from None
        try:
            isi = r.json()
        except ValueError:
            raise GalatTelegram(f'{metode}: balasan bukan JSON (HTTP {r.status_code})') from None
        if not isi.get('ok'):
            raise GalatTelegram(f"{metode}: {isi.get('description', 'gagal')} (kode {isi.get('error_code')})")
        return isi['result']

    def segarkan(self):
        """Buang koneksi lama di pool (mis. yang sudah diputus jaringan/NAT tanpa kabar). Dipakai sebelum kirim ulang."""
        self._sesi.close()

    def saya(self):
        return self.panggil('getMe')

    def hapus_webhook(self):
        return self.panggil('deleteWebhook')

    def atur_perintah(self, perintah):
        return self.panggil('setMyCommands', commands=[{'command': k, 'description': v} for k, v in perintah])

    def pembaruan(self, offset=None, tunggu=0):
        """getUpdates dengan long polling `tunggu` detik."""
        return self.panggil('getUpdates', batas_detik=tunggu + 10, offset=offset, timeout=int(tunggu),
                            allowed_updates=['message', 'callback_query'])

    def kirim(self, chat_id, teks, senyap=False, tombol=None, batas_detik=12):
        """Batas 12 detik (bukan 30): kalau jaringan macet, replay tidak tertahan lama; PengirimTelegram mencoba
        sekali lagi."""
        return self.panggil('sendMessage', batas_detik=batas_detik, chat_id=chat_id, text=teks,
                            disable_notification='true' if senyap else 'false', reply_markup=tombol)

    def hapus_tombol(self, chat_id, message_id):
        return self.panggil('editMessageReplyMarkup', chat_id=chat_id, message_id=message_id,
                            reply_markup={'inline_keyboard': []})

    def jawab_tombol(self, callback_id, teks=None):
        return self.panggil('answerCallbackQuery', callback_query_id=callback_id, text=teks)
