import calendar
from datetime import datetime

import gspread
from google.oauth2.service_account import Credentials

from config import GOOGLE_SHEET_ID, SERVICE_ACCOUNT_FILE

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

MONTH_NAMES = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def _col_letter(col_num: int) -> str:
    result = ""
    while col_num > 0:
        col_num -= 1
        result = chr(65 + col_num % 26) + result
        col_num //= 26
    return result


def get_client():
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPE)
    return gspread.authorize(creds)


def get_sheet(date: datetime):
    client = get_client()
    sh = client.open_by_key(GOOGLE_SHEET_ID)

    month_name = MONTH_NAMES[date.month - 1]

    try:
        worksheet = sh.worksheet(month_name)
    except gspread.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=month_name, rows=200, cols=50)
        _init_month_sheet(worksheet, date)

    return worksheet


def _init_month_sheet(worksheet, date: datetime):
    days_in_month = calendar.monthrange(date.year, date.month)[1]

    headers = ["Nama", "Kode Pegawai"]
    headers += [str(d) for d in range(1, days_in_month + 1)]
    headers += ["Hadir", "Tidak", "% Kehadiran"]
    worksheet.update("A1", [headers])

    last_date_col = 2 + days_in_month
    hadir_col = last_date_col + 1
    tidak_col = last_date_col + 2
    persen_col = last_date_col + 3

    try:
        client = get_client()
        sh = client.open_by_key(GOOGLE_SHEET_ID)
        source = sh.worksheet("Januari")
        employees = source.get("A2:B")
        if employees:
            employees = [row for row in employees if row and row[0]]
            if employees:
                worksheet.update(f"A2:B{1 + len(employees)}", employees)

                formulas = []
                for row in range(2, 2 + len(employees)):
                    date_range = f"C{row}:{_col_letter(last_date_col)}{row}"
                    hadir_f = f'=COUNTIF({date_range},1)'
                    tidak_f = f'=COUNTIF({date_range},0)'
                    persen_f = (
                        f'=IFERROR({_col_letter(hadir_col)}{row}/'
                        f'({_col_letter(hadir_col)}{row}+{_col_letter(tidak_col)}{row})*100,"")'
                    )
                    formulas.append([hadir_f, tidak_f, persen_f])

                recap_range = f"{_col_letter(hadir_col)}2:{_col_letter(persen_col)}{1 + len(employees)}"
                worksheet.update(recap_range, formulas, value_input_option="USER_ENTERED")
    except Exception:
        pass


def find_employee_row(worksheet, nama: str = None, kode: str = None) -> int | None:
    records = worksheet.get("A2:B")

    for i, row_data in enumerate(records, start=2):
        if row_data and len(row_data) >= 2:
            cell_name = str(row_data[0]).strip().lower() if row_data[0] else ""
            cell_kode = str(row_data[1]).strip().lower() if row_data[1] else ""

            if nama:
                input_nama = nama.strip().lower()
                if input_nama == cell_name or (len(input_nama) > 2 and input_nama in cell_name):
                    return i
            if kode:
                input_kode = kode.strip().lower()
                if input_kode == cell_kode:
                    return i

    return None


def update_attendance(nama: str = None, kode_pegawai: str = None, tanggal: str = None, status: str = None) -> dict:
    date = datetime.strptime(tanggal, "%Y-%m-%d")
    worksheet = get_sheet(date)

    row = find_employee_row(worksheet, nama, kode_pegawai)

    if not row:
        client = get_client()
        sh = client.open_by_key(GOOGLE_SHEET_ID)
        for month in MONTH_NAMES:
            try:
                ws = sh.worksheet(month)
                row = find_employee_row(ws, nama, kode_pegawai)
                if row:
                    nama_val = ws.cell(row, 1).value
                    kode_val = ws.cell(row, 2).value
                    worksheet.update_cell(row, 1, nama_val)
                    worksheet.update_cell(row, 2, kode_val)
                    break
            except gspread.WorksheetNotFound:
                continue

    if not row:
        pegawai = nama or kode_pegawai or "tidak dikenal"
        return {"success": False, "message": f"❌ Pegawai '{pegawai}' tidak ditemukan di sheet"}

    value = 1 if status == "hadir" else 0
    col = 2 + date.day

    worksheet.update_cell(row, col, value)

    nama_display = worksheet.cell(row, 1).value or nama or "Pegawai"
    status_display = "hadir ✅" if status == "hadir" else "tidak hadir ❌"
    tanggal_display = date.strftime("%d %B %Y")

    return {
        "success": True,
        "message": f"✅ {nama_display} tercatat {status_display} pada {tanggal_display}",
    }
