import json
import os
import sys
import traceback

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gemini_parser
import sheets
from config import TELEGRAM_TOKEN

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


class handler:
    def __init__(self, environ, start_response):
        self.environ = environ
        self.start_response = start_response

    def __iter__(self):
        method = self.environ["REQUEST_METHOD"]
        content_length = int(self.environ.get("CONTENT_LENGTH", 0))
        body = self.environ["wsgi.input"].read(content_length) if content_length else b""

        if method == "POST":
            try:
                update = json.loads(body)
                self.process_update(update)
            except Exception:
                pass

        self.start_response("200 OK", [("Content-Type", "application/json")])
        yield json.dumps({"ok": True}).encode()

    def process_update(self, update):
        if "message" not in update:
            return

        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "").strip()

        if not text:
            return

        if text.startswith("/start"):
            self.send_message(
                chat_id,
                "🤖 *Bot Absensi Siap!*\n\n"
                "Kirim pesan seperti:\n"
                "• `Budi hadir 15 Maret 2024`\n"
                "• `EMP003 ❌ 20-01-2024`\n"
                "• `siti tidak masuk 15 jan 2024`",
            )
            return

        if text.startswith("/help"):
            self.send_message(
                chat_id,
                "Kirim pesan dengan nama/kode pegawai + tanggal + status hadir/tidak.\n"
                "Bot akan otomatis memahami format apapun.",
            )
            return

        try:
            parsed = gemini_parser.parse_attendance_message(text)
            if not parsed.get("tanggal") or not parsed.get("status"):
                self.send_message(
                    chat_id,
                    "❌ Tidak bisa memahami pesan. Pastikan menyertakan "
                    "nama/kode pegawai, tanggal, dan status hadir/tidak hadir.",
                )
                return
            result = sheets.update_attendance(**parsed)
            self.send_message(chat_id, result["message"])
        except Exception as e:
            traceback.print_exc()
            self.send_message(chat_id, f"❌ Error: {str(e)}")

    def send_message(self, chat_id, text):
        url = f"{TELEGRAM_API}/sendMessage"
        try:
            requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=15)
        except Exception:
            requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
