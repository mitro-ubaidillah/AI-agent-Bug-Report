from fastapi import FastAPI, Query
import json
from pathlib import Path
from datetime import datetime, timezone

app = FastAPI(title="Transfer App (Dummy)")
DATA_FILE = Path(__file__).parent / "data" / "transactions.json"


def load_data():
    with open(DATA_FILE) as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


@app.get("/transfer/logs")
def get_logs(user_id: str = Query(None)):
    data = load_data()
    if user_id:
        data = [t for t in data if t["user_id"] == user_id]
    return {"status": "ok", "data": data}


@app.post("/transfer")
def create_transfer(user_id: str, amount: float, to: str, status: str = "success"):
    data = load_data()
    new_id = max(t["id"] for t in data) + 1 if data else 1
    tx = {
        "id": new_id,
        "user_id": user_id,
        "amount": amount,
        "from": user_id,
        "to": to,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
    }
    data.append(tx)
    save_data(data)
    return {"status": "ok", "data": tx}
