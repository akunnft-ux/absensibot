"""
Set webhook URL untuk Vercel.
Jalankan SETELAH deploy ke Vercel:

    python set_webhook.py https://namaproject.vercel.app
"""

import sys
import requests
from config import TELEGRAM_TOKEN

if len(sys.argv) < 2:
    print("Usage: python set_webhook.py https://namaproject.vercel.app")
    sys.exit(1)

base_url = sys.argv[1].rstrip("/")
webhook_url = f"{base_url}/api/webhook"

resp = requests.post(
    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook",
    json={"url": webhook_url},
)

data = resp.json()
if data.get("ok"):
    print(f"✅ Webhook set ke: {webhook_url}")
else:
    print(f"❌ Gagal: {data}")
