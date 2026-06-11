"""
Fraud Detection Rule — FRD App (Dummy)
BUG: Rule ini mendeteksi fraud jika user melakukan >= 3 transaksi,
TANPA mengecek apakah nominal meningkat tajam.

Seharusnya: fraud hanya jika 3x transfer nominal meningkat tajam (misal: 1jt, 1jt, 100jt)
Realita:   fraud jika 3x transfer APAPUN
"""


def is_fraud(transactions: list) -> dict:
    """
    Cek apakah transaksi mencurigakan (fraud).

    Parameter:
        transactions: list of dicts dengan key 'user_id', 'amount', 'timestamp'

    Returns:
        dict dengan key 'is_fraud' (bool) dan 'reason' (str)
    """
    if len(transactions) >= 3:
        # ======================
        # BUG: tidak ada pengecekan pola peningkatan nominal
        # Semua user dengan >=3 transaksi dianggap fraud
        # ======================
        amounts = [t["amount"] for t in transactions[-3:]]
        return {
            "is_fraud": True,
            "reason": f"Fraud terdeteksi: {len(transactions)} transaksi dalam waktu dekat. "
                      f"Nominal: {amounts}",
            "bug_evidence": (
                "Bug pada baris ini: kondisi hanya mengecek jumlah transaksi (>=3) "
                "tanpa memverifikasi pola peningkatan nominal. "
                "Seharusnya ada pengecekan: amounts[2] >= amounts[1] * 10 AND amounts[1] >= amounts[0]"
            )
        }

    return {
        "is_fraud": False,
        "reason": f"Hanya {len(transactions)} transaksi, tidak memenuhi threshold fraud."
    }
