from fastapi import FastAPI, Body
from fraud_rule import is_fraud
from pathlib import Path
import inspect

app = FastAPI(title="FRD App - Fraud Detection (Dummy with Bug)")


@app.post("/frd/check")
def check_fraud(transactions: list = Body(...)):
    result = is_fraud(transactions)
    return {"status": "ok", "data": result}


@app.get("/frd/code")
def get_fraud_rule_code():
    rule_file = Path(__file__).parent / "fraud_rule.py"
    code = rule_file.read_text()
    return {"status": "ok", "data": {"filename": "fraud_rule.py", "code": code}}
