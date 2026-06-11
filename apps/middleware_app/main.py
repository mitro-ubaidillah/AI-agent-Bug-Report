from fastapi import FastAPI, HTTPException
from datetime import datetime, timezone
import json
from pathlib import Path
import httpx

app = FastAPI(title="Middleware App (Dummy)")
LOG_FILE = Path(__file__).parent / "middleware.log"

TRANSFER_APP_URL = "http://127.0.0.1:8001"
FRD_APP_URL = "http://127.0.0.1:8002"


def log_routing(msg: str):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now(timezone.utc).isoformat()}] {msg}\n")


@app.post("/middleware/process-transfer")
def process_transfer(user_id: str, amount: float, to: str):
    log_routing(f"--- START TRANSACTION PROCESS ---")
    log_routing(f"Processing transfer request: user={user_id} amount=Rp{amount:,.0f} to={to}")

    try:
        with httpx.Client(timeout=5) as client:
            # 1. Fetch user's previous transaction history
            log_routing(f"Fetching transaction logs for user={user_id} from Transfer App...")
            logs_resp = client.get(f"{TRANSFER_APP_URL}/transfer/logs", params={"user_id": user_id})
            if logs_resp.status_code != 200:
                raise HTTPException(500, f"Failed to fetch logs from Transfer App. Code: {logs_resp.status_code}")
            
            previous_txs = logs_resp.json().get("data", [])
            log_routing(f"Retrieved {len(previous_txs)} previous transactions.")

            # 2. Append the new transaction proposal
            new_tx_proposal = {
                "user_id": user_id,
                "amount": amount,
                "from": user_id,
                "to": to,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "status": "pending"
            }
            full_tx_history = previous_txs + [new_tx_proposal]

            # 3. Call FRD App to check for fraud
            log_routing(f"Forwarding full transaction history ({len(full_tx_history)} items) to FRD App for analysis...")
            frd_resp = client.post(f"{FRD_APP_URL}/frd/check", json=full_tx_history)
            if frd_resp.status_code != 200:
                raise HTTPException(500, f"Failed to check fraud from FRD App. Code: {frd_resp.status_code}")
            
            frd_result = frd_resp.json().get("data", {})
            is_fraud_decision = frd_result.get("is_fraud", False)
            fraud_reason = frd_result.get("reason", "")
            
            final_status = "blocked" if is_fraud_decision else "success"
            log_routing(f"FRD Decision: is_fraud={is_fraud_decision}. Reason: '{fraud_reason}'. Final Status={final_status.upper()}")

            # 4. Commit the transaction to Transfer App with its final status
            log_routing(f"Committing transaction to Transfer App with status={final_status}...")
            commit_resp = client.post(
                f"{TRANSFER_APP_URL}/transfer",
                params={"user_id": user_id, "amount": amount, "to": to, "status": final_status}
            )
            if commit_resp.status_code != 200:
                raise HTTPException(500, f"Failed to commit transaction to Transfer App. Code: {commit_resp.status_code}")
            
            committed_tx = commit_resp.json().get("data", {})
            log_routing(f"Transaction committed successfully. Tx ID: {committed_tx.get('id')}")
            log_routing(f"--- END TRANSACTION PROCESS (SUCCESS) ---\n")

            return {
                "status": "ok",
                "message": f"Transfer Rp{amount:,.0f} dari {user_id} ke {to} diproses dengan status: {final_status.upper()}.",
                "data": {
                    "transaction": committed_tx,
                    "fraud_check": {
                        "is_fraud": is_fraud_decision,
                        "reason": fraud_reason
                    }
                }
            }

    except httpx.RequestError as exc:
        err_msg = f"HTTP communication error: {exc}"
        log_routing(f"ERROR: {err_msg}")
        log_routing(f"--- END TRANSACTION PROCESS (FAILED) ---\n")
        raise HTTPException(500, err_msg)
    except Exception as exc:
        err_msg = f"Unexpected error: {exc}"
        log_routing(f"ERROR: {err_msg}")
        log_routing(f"--- END TRANSACTION PROCESS (FAILED) ---\n")
        raise HTTPException(500, err_msg)


@app.get("/middleware/logs")
def get_logs():
    if not LOG_FILE.exists():
        return {"status": "ok", "data": []}
    lines = LOG_FILE.read_text().strip().split("\n")
    return {"status": "ok", "data": lines}
