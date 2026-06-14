"""
Setup awal Google Sheet untuk bot absensi.
Jalankan: python setup_sheet.py

Sebelum menjalankan:
1. Buat file .env dari .env.example
2. Isi SERVICE_ACCOUNT_FILE dengan path ke credentials.json
3. Isi GOOGLE_SHEET_ID (atau biarkan kosong untuk buat sheet baru)
4. Pastikan credentials.json ada di folder yang sama
"""

import calendar
import os
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

MONTH_NAMES = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

DUMMY_EMPLOYEES = [
    ("Budi Santoso", "EMP001"),
    ("Siti Rahayu", "EMP002"),
    ("Ahmad Fauzi", "EMP003"),
    ("Dewi Lestari", "EMP004"),
    ("Rudi Hermawan", "EMP005"),
    ("Ani Kusuma", "EMP006"),
    ("Agus Pratama", "EMP007"),
    ("Rina Wijaya", "EMP008"),
    ("Dodi Suryadi", "EMP009"),
    ("Maya Indah", "EMP010"),
]


def _col_letter(col_num: int) -> str:
    result = ""
    while col_num > 0:
        col_num -= 1
        result = chr(65 + col_num % 26) + result
        col_num //= 26
    return result


def main():
    load_dotenv()

    service_account_file = os.getenv("SERVICE_ACCOUNT_FILE", "credentials.json")
    sheet_id = os.getenv("GOOGLE_SHEET_ID")

    if not os.path.exists(service_account_file):
        print(f"❌ File {service_account_file} tidak ditemukan!")
        print("   Download credentials.json dari Google Cloud Console.")
        return

    creds = Credentials.from_service_account_file(service_account_file, scopes=SCOPE)
    client = gspread.authorize(creds)

    if sheet_id:
        try:
            sh = client.open_by_key(sheet_id)
            print(f"✅ Menggunakan sheet yang sudah ada: {sh.title}")
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"❌ Sheet dengan ID {sheet_id} tidak ditemukan.")
            print("   Periksa GOOGLE_SHEET_ID di .env atau biarkan kosong untuk buat baru.")
            return
    else:
        sh = client.create("Absensi Karyawan")
        print(f"✅ Spreadsheet baru dibuat: {sh.title}")
        print(f"🔗 URL: {sh.url}")
        print(f"🆔 ID: {sh.id}")
        print("")
        print("⚠️  Copy Sheet ID di atas ke .env sebagai GOOGLE_SHEET_ID")
        print("⚠️  Share sheet ini ke email Google pribadimu agar bisa dilihat!")
        print("")

    current_year = datetime.now().year

    for i, month_name in enumerate(MONTH_NAMES):
        month_num = i + 1
        days_in_month = calendar.monthrange(current_year, month_num)[1]

        try:
            worksheet = sh.worksheet(month_name)
            print(f"  ⏭  Sheet '{month_name}' sudah ada, dilewati.")
            continue
        except gspread.WorksheetNotFound:
            pass

        if i == 0:
            worksheet = sh.sheet1
            worksheet.update_title(month_name)
        else:
            worksheet = sh.add_worksheet(title=month_name, rows=200, cols=50)

        headers = ["Nama", "Kode Pegawai"]
        headers += [str(d) for d in range(1, days_in_month + 1)]
        headers += ["Hadir", "Tidak", "% Kehadiran"]
        worksheet.update("A1", [headers])

        employee_rows = [[nama, kode] for nama, kode in DUMMY_EMPLOYEES]
        worksheet.update(f"A2:B{1 + len(employee_rows)}", employee_rows)

        last_date_col = 2 + days_in_month
        hadir_col = last_date_col + 1
        tidak_col = last_date_col + 2
        persen_col = last_date_col + 3

        formulas = []
        for row in range(2, 2 + len(DUMMY_EMPLOYEES)):
            date_range = f"C{row}:{_col_letter(last_date_col)}{row}"
            hadir_f = f'=COUNTIF({date_range},1)'
            tidak_f = f'=COUNTIF({date_range},0)'
            persen_f = (
                f'=IFERROR({_col_letter(hadir_col)}{row}/'
                f'({_col_letter(hadir_col)}{row}+{_col_letter(tidak_col)}{row})*100,"")'
            )
            formulas.append([hadir_f, tidak_f, persen_f])

        recap_range = f"{_col_letter(hadir_col)}2:{_col_letter(persen_col)}{1 + len(DUMMY_EMPLOYEES)}"
        worksheet.update(recap_range, formulas, value_input_option="USER_ENTERED")

        print(f"  ✅ Sheet '{month_name}' ({days_in_month} hari) dibuat dengan {len(DUMMY_EMPLOYEES)} pegawai")

    print("")
    print("🎉 Setup selesai! Semua 12 sheet siap digunakan.")
    print("   Jalankan: python bot.py")


if __name__ == "__main__":
    main()
