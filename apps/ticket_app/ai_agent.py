import httpx
from datetime import datetime, timezone
from pathlib import Path
from pdf_generator import generate_pdf_report
from email_sender import send_simulated_email

TRANSFER_APP_URL = "http://localhost:8001"
FRD_APP_URL = "http://localhost:8002"
MIDDLEWARE_APP_URL = "http://localhost:8003"


async def investigate(ticket_id: str, user_id: str, description: str) -> dict:
    async with httpx.AsyncClient(timeout=10) as client:
        # 1. Ambil log transaksi user dari Transfer App
        logs_resp = await client.get(
            f"{TRANSFER_APP_URL}/transfer/logs",
            params={"user_id": user_id}
        )
        logs_data = logs_resp.json().get("data", [])

        # 2. Ambil source code FRD rule
        code_resp = await client.get(f"{FRD_APP_URL}/frd/code")
        code_data = code_resp.json().get("data", {})
        frd_code = code_data.get("code", "")

        # 3. Ambil log middleware
        mid_resp = await client.get(f"{MIDDLEWARE_APP_URL}/middleware/logs")
        mid_logs = mid_resp.json().get("data", [])

    # 4. Analisa: deteksi bug di FRD rule (dengan membersihkan komentar dan string literal)
    bug_detected = False
    bug_evidence = ""

    clean_code_lines = []
    for line in frd_code.split("\n"):
        # Hapus komentar inline
        if "#" in line:
            line = line.split("#")[0]
        # Abaikan baris yang mendefinisikan string bukti kesalahan agar tidak salah deteksi
        if '"' in line or "'" in line:
            continue
        clean_code_lines.append(line)
    clean_code = "\n".join(clean_code_lines)

    if ">= 3" in frd_code and "amounts[2]" not in clean_code:
        bug_detected = True
        bug_evidence = (
            "Bug terdeteksi: Rule fraud hanya mengecek jumlah transaksi (>= 3) "
            "tanpa memverifikasi pola peningkatan nominal. "
            "Seharusnya: fraud hanya jika 3 transfer berturut-turut dengan "
            "nominal meningkat tajam (contoh: 1jt, 1jt, 100jt)."
        )

    # 5. Format bukti log
    evidence_logs = []
    for tx in logs_data:
        evidence_logs.append(
            f"[{tx.get('timestamp', 'N/A')}] "
            f"user={tx.get('user_id')} "
            f"amount=Rp{tx.get('amount'):,.0f} "
            f"to={tx.get('to')} "
            f"status={tx.get('status')}"
        )

    # 6. Format bukti code (ambil baris relevan)
    code_lines = frd_code.split("\n")
    evidence_code_lines = []
    capture = False
    for line in code_lines:
        capture = capture or "def is_fraud" in line
        if capture:
            evidence_code_lines.append(line)

    # 7. Tentukan team assignment
    if bug_detected:
        assigned_team = "FRD Team"
    else:
        assigned_team = "Transfer Team"

    # 8. Buat report
    report_id = f"RPT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    generated_at = datetime.now(timezone.utc).isoformat()

    if bug_detected:
        summary = (
            f"User {user_id} melaporkan: '{description}'. "
            f"Ditemukan bug pada FRD App: rule fraud salah konfigurasi. "
            f"User memiliki {len(logs_data)} transaksi terakhir yang semuanya "
            f"terblokir oleh fraud detection meskipun polanya normal."
        )
        root_cause = (
            f"File: fraud_rule.py, fungsi is_fraud().\n"
            f"Kondisi `if len(transactions) >= 3` seharusnya ditambah validasi "
            f"pola peningkatan nominal. Rule saat ini memblokir SEMUA user dengan "
            f">= 3 transaksi, tanpa memeriksa apakah nominal meningkat tajam."
        )
        recommendation = (
            "1. Tambahkan pengecekan pola peningkatan nominal di fraud_rule.py.\n"
            "2. Contoh fix:\n"
            f"   if len(transactions) >= 3:\n"
            f"       amounts = [t['amount'] for t in transactions[-3:]]\n"
            f"       if amounts[2] >= amounts[1] * 10 and amounts[1] >= amounts[0]:\n"
            f"           return True\n"
            "3. Lakukan regression test untuk memastikan rule lama tidak broken."
        )
    else:
        summary = f"User {user_id} melaporkan: '{description}'. Tidak ditemukan anomali pada sistem."
        root_cause = "Belum diketahui. Perlu investigasi lebih lanjut oleh tim terkait."
        recommendation = "1. Periksa log aplikasi transfer secara manual.\n2. Hubungi tim terkait."

    report_data = {
        "report_id": report_id,
        "ticket_id": ticket_id,
        "user_id": user_id,
        "generated_at": generated_at,
        "assigned_team": assigned_team,
        "summary": summary,
        "root_cause": root_cause,
        "evidence_logs": evidence_logs,
        "evidence_code": evidence_code_lines,
        "recommendation": recommendation,
        "bug_detected": bug_detected,
    }

    # 9. Generate PDF
    pdf_path = generate_pdf_report(report_data)

    # 9.5 Send simulated email
    pdf_filename = Path(pdf_path).name
    email_subject = f"[ALERT] Incident Investigation Report - {report_id} ({ticket_id})"
    email_body = (
        f"Hi {assigned_team},\n\n"
        f"AI Agent has completed the investigation for Ticket {ticket_id} ('{description}').\n\n"
        f"Summary:\n{summary}\n\n"
        f"Root Cause Analysis:\n{root_cause}\n\n"
        f"Please find the detailed PDF investigation report attached.\n\n"
        f"Regards,\n"
        f"Antigravity AI Agent Investigator"
    )
    
    email_record = send_simulated_email(
        to_team=assigned_team,
        subject=email_subject,
        body=email_body,
        pdf_filename=pdf_filename,
        pdf_path=pdf_path
    )

    report_data["pdf_path"] = pdf_path
    report_data["delivery_status"] = f"Email simulasi terkirim ke {email_record['to']} (ID: {email_record['email_id']})"

    return report_data
