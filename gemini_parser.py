import json
import re

import google.generativeai as genai

from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")


def parse_attendance_message(message: str) -> dict:
    prompt = f"""Kamu adalah assistant parsing data absensi karyawan.
Ekstrak informasi dari pesan user dan kembalikan JSON valid (tanpa markdown, tanpa formatting):

{{
  "nama": string | null,
  "kode_pegawai": string | null,
  "tanggal": string | null (format YYYY-MM-DD),
  "status": "hadir" | "tidak hadir"
}}

Contoh:
User: "Budi hadir 15 Januari 2024"
JSON: {{"nama": "Budi", "kode_pegawai": null, "tanggal": "2024-01-15", "status": "hadir"}}

User: "EMP003 tidak masuk 20-01-2024"
JSON: {{"nama": null, "kode_pegawai": "EMP003", "tanggal": "2024-01-20", "status": "tidak hadir"}}

User: "siti rahayu ❌ 20 jan 2024"
JSON: {{"nama": "Siti Rahayu", "kode_pegawai": null, "tanggal": "2024-01-20", "status": "tidak hadir"}}

User: "Budi ✅ 15 january 2024"
JSON: {{"nama": "Budi", "kode_pegawai": null, "tanggal": "2024-01-15", "status": "hadir"}}

User: "{message}"
JSON:"""

    response = model.generate_content(prompt)
    text = response.text.strip()

    text = re.sub(r'```(?:json)?\s*', '', text).strip()

    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        text = json_match.group()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(f"Gagal parse response Gemini: {text}")
