from fpdf import FPDF
from pathlib import Path

OUTPUT = Path(__file__).parent / "BRD.pdf"

pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=20)

def chapter_title(title):
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

def chapter_body(text):
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 6, text)
    pdf.ln(2)

def bullet(text):
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(5, 6, "- ")
    pdf.write(6, text)
    pdf.ln(6)

def code_block(text):
    pdf.set_font("Courier", "", 8)
    pdf.multi_cell(0, 4, text)
    pdf.ln(2)

# === COVER ===
pdf.add_page()
pdf.ln(40)
pdf.set_font("Helvetica", "B", 24)
pdf.cell(0, 15, "Business Requirement Document", new_x="LMARGIN", new_y="NEXT", align="C")
pdf.ln(5)
pdf.set_font("Helvetica", "B", 18)
pdf.cell(0, 12, "Ticket Investigation System", new_x="LMARGIN", new_y="NEXT", align="C")
pdf.ln(10)
pdf.set_font("Helvetica", "", 12)
pdf.cell(0, 8, "End-to-End Prototype", new_x="LMARGIN", new_y="NEXT", align="C")
pdf.cell(0, 8, "Versi 1.0 - Juni 2026", new_x="LMARGIN", new_y="NEXT", align="C")

# === PAGE 1: Ringkasan ===
pdf.add_page()
chapter_title("1. Ringkasan Eksekutif")
chapter_body(
    "Sistem ini adalah prototype end-to-end untuk investigasi masalah transfer yang dilaporkan user.\n"
    "User membuka ticket -> AI Agent secara otomatis mengumpulkan bukti dari log transfer, "
    "source code aplikasi terkait (Transfer, FRD, Middleware) -> mengidentifikasi kesalahan -> "
    "generate PDF report -> kirim ke tim pemilik.\n\n"
    "Terdapat 3 tim dengan aplikasi dummy masing-masing:\n"
    "- Team Transfer - Aplikasi transfer (pencatatan transaksi)\n"
    "- Team FRD - Aplikasi Fraud Detection (rule-based)\n"
    "- Team Middleware - Aplikasi middleware (orchestrator)"
)

# === PAGE 2: Aktor & Arsitektur ===
chapter_title("2. Aktor & Peran")
pdf.set_font("Helvetica", "B", 10)
pdf.cell(40, 7, "Aktor", border=1)
pdf.cell(140, 7, "Deskripsi", border=1, new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
rows = [
    ("User", "Nasabah yang mengalami masalah transfer. Membuka ticket."),
    ("AI Agent", "Otomatis mengecek log & code aplikasi terkait, menyusun report."),
    ("Team Transfer", "Pemilik aplikasi transfer - menerima report jika masalah di transfer."),
    ("Team FRD", "Pemilik aplikasi fraud detection - menerima report jika masalah di FRD."),
    ("Team Middleware", "Pemilik middleware - menerima report jika masalah di middleware."),
]
for a, b in rows:
    pdf.cell(40, 7, a, border=1)
    pdf.cell(140, 7, b, border=1, new_x="LMARGIN", new_y="NEXT")

pdf.ln(5)
chapter_title("3. Arsitektur Sistem")
chapter_body(
    "Ticket App (User buka ticket -> AI Agent Investigate)\n"
    "  |--- AI Agent: ambil log Transfer App\n"
    "  |--- AI Agent: ambil code FRD App\n"
    "  |--- AI Agent: analisa dan generate PDF Report\n"
    "  |--- AI Agent: kirim PDF ke Team terkait\n"
    "         |\n"
    "    +----+----+\n"
    "    |    |    |\n"
    " Transfer  FRD   Middleware\n"
    " App      App   App"
)

# === PAGE 3: Alur End-to-End ===
pdf.add_page()
chapter_title("4. Alur End-to-End")
alur = (
    "1. USER melaporkan: 'Transfer saya ditolak padahal saldo cukup'\n"
    "2. TICKET APP -> buka ticket baru (status: open)\n"
    "3. AI AGENT mulai investigasi:\n"
    "    - GET /transfer/logs -> ambil log transaksi\n"
    "    - GET /frd/code -> ambil source code fraud rule\n"
    "    - GET /middleware/logs -> ambil log middleware\n"
    "4. AI AGENT analisa:\n"
    "    - Cocokkan log dengan code\n"
    "    - Temukan anomali: rule FRD salah konfigurasi\n"
    "    - Kumpulkan bukti (log, baris code)\n"
    "5. AI AGENT generate PDF Report:\n"
    "    - Ringkasan insiden, RCA, bukti, rekomendasi\n"
    "6. AI AGENT kirim PDF ke Team FRD (dummy)\n"
    "7. Ticket status: resolved"
)
chapter_body(alur)

chapter_title("5. Lingkup")
chapter_body("IN-SCOPE:")
bullet("Aplikasi Transfer App (dummy): API catat transfer, simpan log JSON")
bullet("Aplikasi FRD App (dummy): API fraud detection dengan rule yang salah")
bullet("Aplikasi Middleware App (dummy): API orchestration sederhana")
bullet("Aplikasi Ticket App: API buka ticket + AI Agent investigasi")
bullet("AI Agent: ambil log, baca code, analisa, generate PDF")
bullet("PDF Report: output cetak dengan temuan dan bukti")
bullet("Pengiriman report: dummy (simpan ke folder output)")
pdf.ln(2)
chapter_body("OUT-OF-SCOPE: UI/Dashboard, Autentikasi, Database riil, Email riil, Deployment.")

# === PAGE 4: Detail Bug FRD ===
pdf.add_page()
chapter_title("6. Detail Bug FRD App")
chapter_body(
    "Aturan yang benar (seharusnya):\n"
    "3x transfer dalam waktu dekat dengan nominal meningkat tajam = fraud.\n"
    "Contoh: 1jt, 1jt, 100jt -> FRAUD (benar)\n\n"
    "Aturan yang salah (realita/bug):\n"
    "3x transfer beruntun APAPUN = fraud.\n"
    "Contoh: 50rb, 75rb, 100rb -> FRAUD (salah - harusnya normal)\n"
    "Contoh: 1jt, 2jt, 5jt -> FRAUD (salah - wajar bisnis baik)\n\n"
    "Penyebab: kondisi hanya mengecek len(transactions) >= 3 tanpa validasi "
    "pola peningkatan nominal."
)

chapter_title("7. Kode Bug (fraud_rule.py)")
code_block(
    "def is_fraud(transactions: list) -> dict:\n"
    "    if len(transactions) >= 3:\n"
    "        # ======================\n"
    "        # BUG: tidak ada pengecekan pola peningkatan nominal\n"
    "        # Semua user dengan >=3 transaksi dianggap fraud\n"
    "        # ======================\n"
    "        amounts = [t['amount'] for t in transactions[-3:]]\n"
    "        return {\n"
    '            "is_fraud": True,\n'
    '            "reason": f"Fraud terdeteksi: {len(transactions)} transaksi"\n'
    "        }\n"
    "    return {\"is_fraud\": False, \"reason\": \"Tidak fraud\"}"
)

chapter_title("8. Kode Fix (seharusnya)")
code_block(
    "def is_fraud(transactions: list) -> dict:\n"
    "    if len(transactions) >= 3:\n"
    "        amounts = [t['amount'] for t in transactions[-3:]]\n"
    "        # Cek kenaikan tajam: 1jt, 1jt, 100jt\n"
    "        if amounts[2] >= amounts[1] * 10 and amounts[1] >= amounts[0]:\n"
    "            return {\"is_fraud\": True, \"reason\": ...}\n"
    "    return {\"is_fraud\": False, \"reason\": \"Tidak fraud\"}"
)

# === PAGE 5: Tech Stack & Checklist ===
pdf.add_page()
chapter_title("9. Tech Stack")
pdf.set_font("Helvetica", "B", 10)
pdf.cell(50, 7, "Komponen", border=1)
pdf.cell(130, 7, "Pilihan", border=1, new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
for komp, pilih in [
    ("Bahasa", "Python 3.9+"),
    ("Framework API", "FastAPI + Uvicorn"),
    ("Storage", "File JSON (dummy)"),
    ("PDF Generation", "fpdf2"),
    ("HTTP Client", "httpx"),
    ("Testing", "curl"),
]:
    pdf.cell(50, 7, komp, border=1)
    pdf.cell(130, 7, pilih, border=1, new_x="LMARGIN", new_y="NEXT")

pdf.ln(5)
chapter_title("10. Kriteria Sukses")
bullet("Semua 4 aplikasi bisa jalan dengan uvicorn masing-masing")
bullet("Transfer App bisa mencatat dan mengembalikan log")
bullet("FRD App dengan bug bisa diakses dan kode-nya bisa dibaca")
bullet("AI Agent bisa mengambil log & code dari aplikasi lain")
bullet("AI Agent berhasil mengidentifikasi bug (rule >= 3 tanpa cek amount)")
bullet("PDF report tergenerate dengan bukti log & code")
bullet("Report terkirim ke folder output team terkait")

# === PAGE 6: Checklist ===
pdf.add_page()
chapter_title("11. Checklist AI Agent (Pembuatan Kode)")
pdf.set_font("Helvetica", "B", 11)
pdf.cell(0, 7, "Tahap 1: Setup Project", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
bullet("Buat struktur folder: apps/transfer_app, apps/frd_app, apps/middleware_app, apps/ticket_app")
bullet("Buat requirements.txt (fastapi, uvicorn, httpx, fpdf2)")
bullet("Siapkan data dummy transaksi di transfer_app/data/transactions.json")

pdf.set_font("Helvetica", "B", 11)
pdf.cell(0, 7, "Tahap 2: Transfer App", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
bullet("GET /transfer/logs - return semua log transaksi")
bullet("POST /transfer - tambah transaksi baru")
bullet("Simpan log ke file JSON")

pdf.set_font("Helvetica", "B", 11)
pdf.cell(0, 7, "Tahap 3: FRD App (dengan Bug)", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
bullet("POST /frd/check - terima daftar transaksi, return fraud decision")
bullet("Implementasi rule dengan bug (>= 3 transaksi = fraud)")
bullet("GET /frd/code - return source code fraud_rule.py sebagai string")

pdf.set_font("Helvetica", "B", 11)
pdf.cell(0, 7, "Tahap 4: Middleware App", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
bullet("POST /middleware/process-transfer - terima transfer, catat log")

pdf.set_font("Helvetica", "B", 11)
pdf.cell(0, 7, "Tahap 5: Ticket App + AI Agent", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
bullet("POST /api/tickets - buka ticket baru")
bullet("GET /api/tickets/:id - status ticket")
bullet("AI Agent: fetch log, fetch code, analisa bug, kumpulkan bukti")
bullet("PDF Generator: generate PDF dengan judul, timestamp, ringkasan, bukti, RCA, rekomendasi")
bullet("Pengiriman: simpan PDF ke folder output/ sesuai team")

pdf.set_font("Helvetica", "B", 11)
pdf.cell(0, 7, "Tahap 6: Testing", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
bullet("Jalankan semua 4 server")
bullet("Test: buka ticket -> investigate -> cek PDF")
bullet("Verifikasi bahwa PDF berisi bukti lengkap")

# === PAGE 7: Cara Menjalankan ===
pdf.add_page()
chapter_title("12. Cara Menjalankan")
code_block(
    "# Terminal 1: Transfer App (port 8001)\n"
    "cd apps/transfer_app && uvicorn main:app --port 8001\n\n"
    "# Terminal 2: FRD App (port 8002)\n"
    "cd apps/frd_app && uvicorn main:app --port 8002\n\n"
    "# Terminal 3: Middleware App (port 8003)\n"
    "cd apps/middleware_app && uvicorn main:app --port 8003\n\n"
    "# Terminal 4: Ticket App (port 8000)\n"
    "cd apps/ticket_app && uvicorn main:app --port 8000\n\n"
    "# Test: Buka ticket\n"
    'curl -X POST "http://localhost:8000/api/tickets'
    '?user_id=USR001&description=Transfer ditolak padahal saldo cukup"\n\n'
    "# Test: Investigasi\n"
    "curl -X POST http://localhost:8000/api/tickets/TKT-001/investigate\n\n"
    "# Test: Download PDF\n"
    "curl -O http://localhost:8000/api/reports/RPT-.../pdf"
)

chapter_title("13. Timeline")
pdf.set_font("Helvetica", "B", 10)
pdf.cell(100, 7, "Tahap", border=1)
pdf.cell(30, 7, "Durasi", border=1, new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Helvetica", "", 10)
for tahap, durasi in [
    ("Setup folder & dependencies", "15 menit"),
    ("Transfer App", "20 menit"),
    ("FRD App (dengan bug)", "20 menit"),
    ("Middleware App", "15 menit"),
    ("Ticket App + AI Agent + PDF", "60 menit"),
    ("Testing end-to-end", "30 menit"),
    ("TOTAL", "~2.5 jam"),
]:
    pdf.cell(100, 7, tahap, border=1)
    pdf.cell(30, 7, durasi, border=1, new_x="LMARGIN", new_y="NEXT")

pdf.output(str(OUTPUT))
print(f"PDF generated: {OUTPUT}")
