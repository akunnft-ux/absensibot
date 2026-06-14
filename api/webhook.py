import json
import os
import sys
import traceback

import requests
from flask import Flask, request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import gemini_parser
import sheets
from config import TELEGRAM_TOKEN

app = Flask(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


@app.route("/api/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True)
    if update:
        process_update(update)
    return {"ok": True}


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def index(path):
    return "Bot Absensi Webhook is running"


def process_update(update):
    if "message" not in update:
        return

    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "").strip()

    if not text:
        return

    if text.startswith("/start"):
        send_message(
            chat_id,
            "🤖 *Bot Absensi Siap!*\n\n"
            "Kirim pesan seperti:\n"
            "• `Budi hadir 15 Maret 2024`\n"
            "• `EMP003 ❌ 20-01-2024`\n"
            "• `siti tidak masuk 15 jan 2024`",
        )
        return

    if text.startswith("/help"):
        send_message(
            chat_id,
            "Kirim pesan dengan nama/kode pegawai + tanggal + status hadir/tidak.\n"
            "Bot akan otomatis memahami format apapun.",
        )
        return

    try:
        parsed = gemini_parser.parse_attendance_message(text)
        if not parsed.get("tanggal") or not parsed.get("status"):
            send_message(
                chat_id,
                "❌ Tidak bisa memahami pesan. Pastikan menyertakan "
                "nama/kode pegawai, tanggal, dan status hadir/tidak hadir.",
            )
            return
        result = sheets.update_attendance(**parsed)
        send_message(chat_id, result["message"])
    except Exception as e:
        traceback.print_exc()
        send_message(chat_id, f"❌ Error: {str(e)}")


def send_message(chat_id, text):
    url = f"{TELEGRAM_API}/sendMessage"
    try:
        requests.post(
            url,
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=15,
        )
    except Exception:
        requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
