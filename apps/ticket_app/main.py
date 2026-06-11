from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, Response, FileResponse
import json
from pathlib import Path
from datetime import datetime, timezone
from ai_agent import investigate
from pdf_generator import OUTPUT_DIR

app = FastAPI(title="Ticket Investigation System")
TICKETS_FILE = Path(__file__).parent / "tickets.json"
REPORTS_FILE = Path(__file__).parent / "reports.json"
EMAILS_FILE = Path(__file__).parent / "emails.json"
TRANSACTIONS_FILE = Path(__file__).parent.parent / "transfer_app" / "data" / "transactions.json"
STATIC_DIR = Path(__file__).parent / "static"


def load_json(path):
    if not path.exists():
        return []
    with open(path) as f:
        try:
            return json.load(f)
        except Exception:
            return []


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


# ==========================================
# Static Frontend Serving Endpoints
# ==========================================

@app.get("/", response_class=HTMLResponse)
def get_dashboard_ui():
    html_file = STATIC_DIR / "index.html"
    if not html_file.exists():
        return HTMLResponse("<h1>Error: index.html not found!</h1>", status_code=404)
    return html_file.read_text(encoding="utf-8")


@app.get("/static/style.css")
def get_css():
    css_file = STATIC_DIR / "style.css"
    if not css_file.exists():
        return Response("/* CSS not found */", status_code=404)
    return Response(css_file.read_text(encoding="utf-8"), media_type="text/css")


@app.get("/static/app.js")
def get_js():
    js_file = STATIC_DIR / "app.js"
    if not js_file.exists():
        return Response("// JS not found", status_code=404)
    return Response(js_file.read_text(encoding="utf-8"), media_type="application/javascript")


# ==========================================
# Dashboard Statistics & Email Endpoints
# ==========================================

@app.get("/api/dashboard/stats")
def get_dashboard_stats():
    tickets = load_json(TICKETS_FILE)
    total_tickets = len(tickets)
    resolved_tickets = len([t for t in tickets if t.get("status") == "resolved"])
    
    # Load transactions from transfer_app data file
    transactions = load_json(TRANSACTIONS_FILE)
    total_tx = len(transactions)
    blocked_tx = len([t for t in transactions if t.get("status") == "blocked"])
    success_tx = len([t for t in transactions if t.get("status") == "success"])

    # Count how many emails have been simulated
    emails = load_json(EMAILS_FILE)
    total_emails = len(emails)

    return {
        "status": "ok",
        "data": {
            "total_tickets": total_tickets,
            "resolved_tickets": resolved_tickets,
            "total_transactions": total_tx,
            "blocked_transactions": blocked_tx,
            "success_transactions": success_tx,
            "total_emails": total_emails
        }
    }


@app.get("/api/emails")
def get_simulated_emails():
    emails = load_json(EMAILS_FILE)
    return {"status": "ok", "data": emails}


# ==========================================
# Ticket & Investigation Endpoints
# ==========================================

@app.post("/api/tickets")
def create_ticket(user_id: str, description: str):
    tickets = load_json(TICKETS_FILE)
    # Ensure tickets is a list
    if not isinstance(tickets, list):
        tickets = []
    ticket_id = f"TKT-{len(tickets) + 1:03d}"
    ticket = {
        "ticket_id": ticket_id,
        "user_id": user_id,
        "description": description,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    tickets.append(ticket)
    save_json(TICKETS_FILE, tickets)
    return {"status": "ok", "data": ticket}


@app.get("/api/tickets")
def get_all_tickets():
    tickets = load_json(TICKETS_FILE)
    return {"status": "ok", "data": tickets}


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    tickets = load_json(TICKETS_FILE)
    for t in tickets:
        if t["ticket_id"] == ticket_id:
            return {"status": "ok", "data": t}
    raise HTTPException(404, "Ticket not found")


@app.post("/api/tickets/{ticket_id}/investigate")
async def run_investigation(ticket_id: str):
    tickets = load_json(TICKETS_FILE)
    ticket = None
    for t in tickets:
        if t["ticket_id"] == ticket_id:
            ticket = t
            break
    if not ticket:
        raise HTTPException(404, "Ticket not found")

    ticket["status"] = "investigating"
    save_json(TICKETS_FILE, tickets)

    try:
        report = await investigate(
            ticket_id=ticket_id,
            user_id=ticket["user_id"],
            description=ticket["description"],
        )
    except Exception as e:
        ticket["status"] = "open"
        save_json(TICKETS_FILE, tickets)
        raise HTTPException(500, f"Investigation failed: {str(e)}")

    reports = load_json(REPORTS_FILE)
    if not isinstance(reports, dict):
        reports = {}
    reports[report["report_id"]] = report
    save_json(REPORTS_FILE, reports)

    ticket["status"] = "resolved"
    ticket["report_id"] = report["report_id"]
    save_json(TICKETS_FILE, tickets)

    return {"status": "ok", "data": report}


@app.get("/api/reports/{report_id}")
def get_report(report_id: str):
    reports = load_json(REPORTS_FILE)
    if not isinstance(reports, dict):
        reports = {}
    report = reports.get(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    return {"status": "ok", "data": report}


@app.get("/api/reports/{report_id}/pdf")
def download_report_pdf(report_id: str):
    reports = load_json(REPORTS_FILE)
    if not isinstance(reports, dict):
        reports = {}
    report = reports.get(report_id)
    if not report:
        raise HTTPException(404, "Report not found")
    pdf_path = Path(report["pdf_path"])
    if not pdf_path.exists():
        raise HTTPException(404, "PDF file not found")
    return FileResponse(str(pdf_path), media_type="application/pdf",
                        filename=f"{report_id}.pdf")


# ==========================================
# Proxy Routes to Bypass Browser CORS
# ==========================================

@app.post("/api/playground/transfer")
def playground_transfer(user_id: str, amount: float, to: str):
    import httpx
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.post(
                "http://127.0.0.1:8003/middleware/process-transfer",
                params={"user_id": user_id, "amount": amount, "to": to}
            )
            return resp.json()
    except Exception as e:
        raise HTTPException(500, f"Failed to contact Middleware: {str(e)}")


@app.get("/api/playground/transactions")
def playground_transactions(user_id: str = None):
    import httpx
    try:
        with httpx.Client(timeout=5) as client:
            params = {}
            if user_id:
                params["user_id"] = user_id
            resp = client.get("http://127.0.0.1:8001/transfer/logs", params=params)
            return resp.json()
    except Exception as e:
        raise HTTPException(500, f"Failed to contact Transfer App: {str(e)}")


@app.get("/api/microservices/logs/{app_name}")
def get_app_logs_proxy(app_name: str):
    import httpx
    try:
        with httpx.Client(timeout=5) as client:
            if app_name == "ticket":
                tickets = load_json(TICKETS_FILE)
                reports = load_json(REPORTS_FILE)
                return {
                    "status": "ok",
                    "data": {
                        "tickets.json": tickets,
                        "reports.json": reports
                    }
                }
            elif app_name == "transfer":
                resp = client.get("http://127.0.0.1:8001/transfer/logs")
                return {"status": "ok", "data": resp.json().get("data", [])}
            elif app_name == "frd":
                resp = client.get("http://127.0.0.1:8002/frd/code")
                return {"status": "ok", "data": resp.json().get("data", {})}
            elif app_name == "middleware":
                resp = client.get("http://127.0.0.1:8003/middleware/logs")
                return {"status": "ok", "data": resp.json().get("data", [])}
            else:
                raise HTTPException(400, "Unknown microservice name")
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch logs from {app_name}: {str(e)}")


