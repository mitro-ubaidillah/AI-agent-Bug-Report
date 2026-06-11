from fpdf import FPDF
from datetime import datetime
import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_pdf_report(report_data: dict) -> str:
    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "Incident Investigation Report", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Report ID    : {report_data['report_id']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Ticket ID    : {report_data['ticket_id']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"User ID      : {report_data['user_id']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Generated At : {report_data['generated_at']}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Assigned Team: {report_data['assigned_team']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # Summary
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "1. Ringkasan Insiden", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(pdf.epw, 6, report_data["summary"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Root Cause
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "2. Root Cause Analysis", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(pdf.epw, 6, report_data["root_cause"], new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Evidence Logs
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "3. Bukti Log Transaksi", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Courier", "", 8)
    if report_data["evidence_logs"]:
        for log_line in report_data["evidence_logs"]:
            pdf.multi_cell(pdf.epw, 4, log_line, new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.multi_cell(pdf.epw, 4, "No logs recorded.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Evidence Code
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "4. Bukti Source Code (FRD Rule)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Courier", "", 8)
    if report_data["evidence_code"]:
        for code_line in report_data["evidence_code"]:
            pdf.multi_cell(pdf.epw, 4, code_line, new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.multi_cell(pdf.epw, 4, "No code snippet attached.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # Recommendation
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "5. Rekomendasi Perbaikan", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(pdf.epw, 6, report_data["recommendation"], new_x="LMARGIN", new_y="NEXT")

    filename = f"{report_data['report_id']}.pdf"
    filepath = OUTPUT_DIR / filename
    pdf.output(str(filepath))
    return str(filepath)
