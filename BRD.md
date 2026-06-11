# BRD – Business Requirement Document
## Ticket Investigation System — End-to-End Prototype

**Versi:** 1.0
**Status:** Draft
**Tipe Proyek:** Prototype (Dummy Apps + AI Agent Simulation)

---

## 1. Ringkasan Eksekutif

Sistem ini adalah prototype end-to-end untuk investigasi **masalah transfer** yang dilaporkan user.  
User membuka ticket → AI Agent secara otomatis mengumpulkan bukti dari **log transfer**, **source code** aplikasi terkait (Transfer, FRD, Middleware) → mengidentifikasi kesalahan → generate **PDF report** → kirim ke **tim pemilik**.

Terdapat **3 tim** dengan aplikasi dummy masing-masing:
- **Team Transfer** — Aplikasi transfer (pencatatan transaksi)
- **Team FRD** — Aplikasi Fraud Detection (rule-based)
- **Team Middleware** — Aplikasi middleware (orchestrator)

---

## 2. Aktor & Peran

| Aktor | Deskripsi |
|---|---|
| **User** | Nasabah yang mengalami masalah transfer. Membuka ticket. |
| **AI Agent** | Otomatis mengecek log & code aplikasi terkait, menyusun report. |
| **Team Transfer** | Pemilik aplikasi transfer — menerima report jika masalah di transfer. |
| **Team FRD** | Pemilik aplikasi fraud detection — menerima report jika masalah di FRD. |
| **Team Middleware** | Pemilik aplikasi middleware — menerima report jika masalah di middleware. |

---

## 3. Arsitektur Sistem

```
┌─────────────────────────────────────────────────────┐
│                   TICKET APP                         │
│  (User buka ticket → AI Agent Investigate)          │
│  ├─ AI Agent: ambil log Transfer App                │
│  ├─ AI Agent: ambil code FRD App                    │
│  ├─ AI Agent: analisa dan generate PDF Report       │
│  └─ AI Agent: kirim PDF ke Team terkait             │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
┌─────────────────┐ ┌─────────┐ ┌───────────┐
│ TRANSFER APP    │ │ FRD APP │ │ MIDDLEWARE │
│ (Dummy)         │ │ (Dummy) │ │ APP (Dummy)│
│ - Catat transfer│ │ - Fraud │ │ - Routing  │
│ - Simpan log    │ │   Rule  │ │ - Logging  │
└─────────────────┘ └─────────┘ └───────────┘
```

---

## 4. Alur End-to-End

```
1. USER melaporkan: "Transfer saya ditolak padahal saldo cukup"
       │
2. TICKET APP → buka ticket baru (status: open)
       │
3. AI AGENT mulai investigasi:
       ├── GET /transfer/logs → ambil log transaksi
       ├── GET /frd/code → ambil source code fraud rule
       ├── GET /middleware/logs → ambil log middleware
       │
4. AI AGENT analisa:
       ├── Cocokkan log dengan code
       ├── Temukan anomali: rule FRD salah konfigurasi
       │   (seharusnya: 3x transfer nominal meningkat tajam = fraud
       │    kenyataan: 3x transfer beruntun = fraud)
       └── Kumpulkan bukti (log, baris code, screenshot text)
       │
5. AI AGENT generate PDF Report:
       ├── Ringkasan insiden
       ├── Root cause analysis
       ├── Bukti log & code
       └── Rekomendasi perbaikan
       │
6. AI AGENT kirim PDF ke Team FRD (dummy email)
       │
7. Ticket status: resolved
```

---

## 5. Lingkup

### In-Scope
- Aplikasi **Transfer App** (dummy): API catat transfer, simpan log JSON
- Aplikasi **FRD App** (dummy): API fraud detection dengan rule yang salah
- Aplikasi **Middleware App** (dummy): API orchestration sederhana
- Aplikasi **Ticket App**: API buka ticket + AI Agent investigasi
- AI Agent: ambil log, baca code, analisa, generate PDF
- PDF Report: output cetak dengan temuan dan bukti
- Pengiriman report: dummy (simpan ke folder output)

### Out-of-Scope
- UI / Dashboard
- Autentikasi & autorisasi
- Database riil (gunakan file JSON)
- Email delivery riil (simulasi simpan ke file)
- Deployment / container

---

## 6. Detail Aplikasi & Skenario Bug

### 6.1 Transfer App (Dummy)
- **Route:** `POST /transfer` — buat transfer baru
- **Route:** `GET /transfer/logs` — ambil log transaksi
- **Route:** `GET /transfer/logs?user_id=xxx` — filter per user
- **Data log:** `{ user_id, amount, timestamp, status }`

### 6.2 FRD App (Dummy) — ❌ Mengandung Bug
- **Route:** `POST /frd/check` — cek apakah transfer fraud
- **Rule (benar):** 3x transfer dalam waktu dekat dengan nominal meningkat tajam (misal 1jt → 1jt → 100jt) = **fraud**
- **Rule (realita/bug):** 3x transfer beruntun APAPUN = **fraud** — karena kondisi `>= 3` bukan `>= 3 AND increasing pattern`
- **Route:** `GET /frd/code` — ekspos source code (untuk AI Agent)

### 6.3 Middleware App (Dummy)
- **Route:** `POST /middleware/process-transfer` — panggil Transfer App + FRD App
- Mencatat log routing

### 6.4 Ticket App (Main)
- **Route:** `POST /api/tickets` — buka ticket baru
- **Route:** `GET /api/tickets/:id` — lihat status ticket
- **Route:** `POST /api/tickets/:id/investigate` — jalankan AI Agent
- **Route:** `GET /api/reports/:id` — download PDF report

---

## 7. Skenario Bug FRD (Detail)

### 7.1 Aturan yang benar (seharusnya):
```python
def is_fraud(transactions):
    if len(transactions) >= 3:
        amounts = [t["amount"] for t in transactions[-3:]]
        # Cek kenaikan tajam: 1jt, 1jt, 100jt
        if amounts[2] >= amounts[1] * 10 and amounts[1] >= amounts[0]:
            return True
    return False
```

### 7.2 Aturan yang salah (bug):
```python
def is_fraud(transactions):
    if len(transactions) >= 3:
        # ❌ BUG: tidak cek nominal, langsung true
        return True
    return False
```

### 7.3 Dampak:
- User A: transfer 50rb, 75rb, 100rb → **terkena fraud** (padahal normal)
- User B: transfer 1jt, 2jt, 5jt → **terkena fraud** (wajar, bisnis baik)
- Harusnya hanya User C: 1jt, 1jt, 100jt → **fraud** yang kena

---

## 8. Tech Stack

| Komponen | Pilihan |
|---|---|
| **Bahasa** | Python 3.11+ |
| **Framework API** | FastAPI + Uvicorn |
| **Storage** | File JSON (dummy) |
| **PDF Generation** | `fpdf2` atau `reportlab` |
| **HTTP Client** | `httpx` |
| **CLI** | `uvicorn`, `curl` untuk test |

---

## 9. Kriteria Sukses

- [x] Semua 4 aplikasi bisa jalan dengan `uvicorn` masing-masing
- [x] Transfer App bisa mencatat dan mengembalikan log
- [x] FRD App dengan bug bisa diakses dan kode-nya bisa dibaca
- [x] AI Agent bisa mengambil log & code dari aplikasi lain
- [x] AI Agent berhasil mengidentifikasi bug (rule `>= 3` tanpa cek amount)
- [x] PDF report tergenerate dengan bukti log & code
- [x] Report terkirim ke folder output team terkait

---

## 10. Checklist untuk AI Agent (Pembuatan Kode)

### Tahap 1: Setup Project
- [ ] Buat struktur folder: `apps/transfer_app`, `apps/frd_app`, `apps/middleware_app`, `apps/ticket_app`
- [ ] Buat `requirements.txt` (fastapi, uvicorn, httpx, fpdf2)
- [ ] Siapkan data dummy transaksi di `transfer_app/data/transactions.json`

### Tahap 2: Transfer App
- [ ] `GET /transfer/logs` — return semua log transaksi
- [ ] `POST /transfer` — tambah transaksi baru
- [ ] Simpan log ke file JSON

### Tahap 3: FRD App (dengan Bug)
- [ ] `POST /frd/check` — terima daftar transaksi, return fraud decision
- [ ] Implementasi rule dengan bug (>= 3 transaksi = fraud)
- [ ] `GET /frd/code` — return source code fraud_rule.py sebagai string

### Tahap 4: Middleware App
- [ ] `POST /middleware/process-transfer` — terima transfer, panggil FRD
- [ ] Catat log routing

### Tahap 5: Ticket App + AI Agent
- [ ] `POST /api/tickets` — buka ticket baru
- [ ] `GET /api/tickets/:id` — status ticket
- [ ] **AI Agent (`ai_agent.py`):**
  - [ ] Fetch log dari Transfer App (`GET /transfer/logs`)
  - [ ] Fetch code dari FRD App (`GET /frd/code`)
  - [ ] Analisa: deteksi rule `>= 3` tanpa cek amount
  - [ ] Kumpulkan bukti (potongan log, potongan code)
- [ ] **PDF Generator (`pdf_generator.py`):**
  - [ ] Generate PDF dengan: judul, timestamp, ringkasan, bukti log, bukti code, root cause, rekomendasi
- [ ] Pengiriman: simpan PDF ke folder `output/` sesuai team

### Tahap 6: Testing
- [ ] Jalankan semua 4 server
- [ ] Test: buka ticket → investigate → cek PDF
- [ ] Verifikasi bahwa PDF berisi bukti lengkap

---

## 11. Cara Menjalankan

```bash
# Terminal 1: Transfer App
cd apps/transfer_app && uvicorn main:app --port 8001

# Terminal 2: FRD App
cd apps/frd_app && uvicorn main:app --port 8002

# Terminal 3: Middleware App
cd apps/middleware_app && uvicorn main:app --port 8003

# Terminal 4: Ticket App
cd apps/ticket_app && uvicorn main:app --port 8000

# Test: Buka ticket
curl -X POST http://localhost:8000/api/tickets \
  -H "Content-Type: application/json" \
  -d '{"user_id": "USR001", "description": "Transfer ditolak padahal saldo cukup"}'

# Test: Investigasi
curl -X POST http://localhost:8000/api/tickets/TKT-001/investigate

# Test: Download PDF
curl -O http://localhost:8000/api/reports/RPT-001/pdf
```

---

## 12. Timeline (Estimasi Pembuatan)

| Tahap | Durasi |
|---|---|
| Setup folder & dependencies | 15 menit |
| Transfer App | 20 menit |
| FRD App (dengan bug) | 20 menit |
| Middleware App | 15 menit |
| Ticket App + AI Agent + PDF | 60 menit |
| Testing end-to-end | 30 menit |
| **Total** | **~2.5 jam** |
