/* ==========================================================================
   Frontend Logic: Interactive Tabs, Stats, Forms & Live AI Simulation
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
    // Current State
    let activeTab = "dashboard";
    let activeLogApp = "ticket";
    let cachedEmails = [];
    let isInvestigating = false;

    // Elements
    const navItems = document.querySelectorAll(".nav-menu .nav-item");
    const tabPanes = document.querySelectorAll(".tab-pane");
    const currentTimeEl = document.getElementById("current-time");
    
    // Stats Elements
    const statTotalTickets = document.getElementById("stat-total-tickets");
    const statResolvedTickets = document.getElementById("stat-resolved-tickets");
    const statSuccessTx = document.getElementById("stat-success-tx");
    const statBlockedTx = document.getElementById("stat-blocked-tx");

    // Forms
    const ticketForm = document.getElementById("ticket-form");
    const playgroundTxForm = document.getElementById("playground-tx-form");

    // Tables
    const ticketsTableBody = document.querySelector("#tickets-table tbody");
    const transactionsTableBody = document.querySelector("#transactions-table tbody");

    // AI Console
    const agentConsole = document.getElementById("agent-console");
    const investigatorStatusBadge = document.getElementById("investigator-status-badge");

    // Emails
    const emailList = document.getElementById("email-list");
    const emailPreviewEmpty = document.getElementById("email-preview-empty");
    const emailPreviewContent = document.getElementById("email-preview-content");
    const emFrom = document.getElementById("em-from");
    const emTo = document.getElementById("em-to");
    const emSubject = document.getElementById("em-subject");
    const emDate = document.getElementById("em-date");
    const emBody = document.getElementById("em-body");
    const emPdfName = document.getElementById("em-pdf-name");
    const emPdfLink = document.getElementById("em-pdf-link");

    // Log Terminal
    const logTabBtns = document.querySelectorAll(".log-tab-btn");
    const logTerminalTitle = document.getElementById("log-terminal-title");
    const logTerminalContent = document.getElementById("log-terminal-content");

    // Modal
    const reportModal = document.getElementById("report-modal");
    const btnCloseModal = document.getElementById("btn-close-modal");
    const btnCloseModalFooter = document.getElementById("btn-close-modal-footer");
    const btnDownloadPdf = document.getElementById("btn-download-pdf");

    // 1. Clock Display (Every second)
    function updateClock() {
        const now = new Date();
        currentTimeEl.textContent = now.toLocaleTimeString("id-ID", { hour12: false });
    }
    setInterval(updateClock, 1000);
    updateClock();

    // 2. Tab Navigation
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");
            switchTab(tabId);
        });
    });

    function switchTab(tabId) {
        activeTab = tabId;
        
        // Update Nav Menu active state
        navItems.forEach(item => {
            if (item.getAttribute("data-tab") === tabId) {
                item.classList.add("active");
            } else {
                item.classList.remove("active");
            }
        });

        // Update Tab Panes active state
        tabPanes.forEach(pane => {
            if (pane.id === `tab-${tabId}`) {
                pane.classList.add("active");
            } else {
                pane.classList.remove("active");
            }
        });

        // Update Header page details
        const titleEl = document.getElementById("page-title");
        const descEl = document.getElementById("page-desc");

        if (tabId === "dashboard") {
            titleEl.textContent = "Dashboard Utama";
            descEl.textContent = "Memonitor tiket investigasi insiden dan mengelola investigasi otomatis berbasis AI Agent.";
            loadDashboardData();
        } else if (tabId === "playground") {
            titleEl.textContent = "Playground Transaksi";
            descEl.textContent = "Simulasikan transfer dana instan antarnasabah dan amati bagaimana Middleware menguji pola fraud.";
            loadPlaygroundData();
        } else if (tabId === "emails") {
            titleEl.textContent = "Simulator Email Keluar";
            descEl.textContent = "Lihat daftar surat keluar berisi laporan investigasi yang telah disimulasikan oleh AI Agent.";
            loadEmailsData();
        } else if (tabId === "logs") {
            titleEl.textContent = "Pusat Log Microservices";
            descEl.textContent = "Melihat aktivitas internal dari masing-masing 4 microservice secara mentah.";
            loadLogsData();
        }
    }

    // 3. Helper to format Currency
    function formatIDR(amount) {
        return new Intl.NumberFormat("id-ID", {
            style: "currency",
            currency: "IDR",
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(amount);
    }

    // ==========================================
    // BACKEND API INTEGRATIONS
    // ==========================================

    // Fetch Stats
    async function loadStats() {
        try {
            const resp = await fetch("/api/dashboard/stats");
            const res = await resp.json();
            if (res.status === "ok") {
                const s = res.data;
                statTotalTickets.textContent = s.total_tickets;
                statResolvedTickets.textContent = s.resolved_tickets;
                statSuccessTx.textContent = s.success_transactions;
                statBlockedTx.textContent = s.blocked_transactions;
            }
        } catch (err) {
            console.error("Error fetching stats:", err);
        }
    }

    // Load Ticket Table
    async function loadTickets() {
        try {
            const resp = await fetch("/api/tickets");
            const res = await resp.json();
            if (res.status === "ok") {
                renderTicketsTable(res.data);
            }
        } catch (err) {
            console.error("Error loading tickets:", err);
        }
    }

    function renderTicketsTable(tickets) {
        if (!tickets || tickets.length === 0) {
            ticketsTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Belum ada tiket yang dibuka.</td></tr>`;
            return;
        }

        ticketsTableBody.innerHTML = "";
        // Sort tickets descending by ID
        tickets.sort((a, b) => b.ticket_id.localeCompare(a.ticket_id));

        tickets.forEach(t => {
            const tr = document.createElement("tr");
            
            let statusBadge = "";
            let actionBtn = "";

            if (t.status === "open") {
                statusBadge = `<span class="badge open">OPEN</span>`;
                actionBtn = `<button class="btn btn-primary btn-sm btn-investigate" data-id="${t.ticket_id}" ${isInvestigating ? "disabled" : ""}>🤖 Investigasi</button>`;
            } else if (t.status === "investigating") {
                statusBadge = `<span class="badge investigating">ANALYZING...</span>`;
                actionBtn = `<button class="btn btn-secondary btn-sm" disabled>⏳ Diproses</button>`;
            } else if (t.status === "resolved") {
                statusBadge = `<span class="badge resolved">RESOLVED</span>`;
                actionBtn = `<button class="btn btn-secondary btn-sm btn-view-report" data-report-id="${t.report_id}">📄 Lihat Hasil</button>`;
            }

            tr.innerHTML = `
                <td><strong>${t.ticket_id}</strong></td>
                <td><span class="badge bg-blue">${t.user_id}</span></td>
                <td>${t.description}</td>
                <td>${statusBadge}</td>
                <td>${actionBtn}</td>
            `;
            ticketsTableBody.appendChild(tr);
        });

        // Add action listeners
        document.querySelectorAll(".btn-investigate").forEach(btn => {
            btn.addEventListener("click", () => {
                const ticketId = btn.getAttribute("data-id");
                triggerAiAgent(ticketId);
            });
        });

        document.querySelectorAll(".btn-view-report").forEach(btn => {
            btn.addEventListener("click", () => {
                const reportId = btn.getAttribute("data-report-id");
                openReportModal(reportId);
            });
        });
    }

    // Submit Ticket Form
    ticketForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const userId = document.getElementById("ticket-user-id").value;
        const description = document.getElementById("ticket-desc").value;

        try {
            const resp = await fetch(`/api/tickets?user_id=${userId}&description=${encodeURIComponent(description)}`, {
                method: "POST"
            });
            const res = await resp.json();
            if (res.status === "ok") {
                // Log event to console
                appendConsoleLog(`[SYSTEM] Tiket Baru berhasil dibuat: ${res.data.ticket_id} (${userId})`, "system-msg");
                loadDashboardData();
            }
        } catch (err) {
            console.error("Error creating ticket:", err);
            appendConsoleLog(`[SYSTEM] Gagal membuat tiket baru: ${err}`, "agent-finding");
        }
    });

    // ==========================================
    // LIVE AI AGENT CONSOLE SIMULATION (MAGIC)
    // ==========================================

    function appendConsoleLog(text, className = "") {
        const p = document.createElement("p");
        p.textContent = text;
        if (className) p.className = className;
        agentConsole.appendChild(p);
        agentConsole.scrollTop = agentConsole.scrollHeight;
    }

    async function triggerAiAgent(ticketId) {
        if (isInvestigating) return;
        isInvestigating = true;
        
        // Refresh ticket list to show investigating status
        const respTickets = await fetch("/api/tickets");
        const resTickets = await respTickets.json();
        if (resTickets.status === "ok") {
            const tickets = resTickets.data;
            const target = tickets.find(tk => tk.ticket_id === ticketId);
            if (target) target.status = "investigating";
            renderTicketsTable(tickets);
        }

        // Set status badge and clear console
        investigatorStatusBadge.textContent = "ACTIVE";
        investigatorStatusBadge.className = "badge investigating";
        agentConsole.innerHTML = "";

        // Animation steps with timing delays
        const delay = (ms) => new Promise(resolve => setTimeout(ms ? resolve : resolve, ms));

        try {
            appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] 🤖 AI Agent Investigator dipicu untuk Tiket: ${ticketId}...`, "system-msg");
            await delay(800);
            
            appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] 🔍 Menghubungi Middleware App di Port 8003 untuk analisis log rute...`, "agent-step");
            await delay(1000);
            
            appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] 📥 Menghubungi Transfer App di Port 8001 untuk mengunduh daftar log transaksi...`, "agent-step");
            await delay(1200);

            // Execute the actual FastAPI investigation API in the background
            const apiPromise = fetch(`/api/tickets/${ticketId}/investigate`, { method: "POST" });
            
            appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] 📂 Menghubungi FRD App di Port 8002 untuk menyalin kode logika anti-fraud (fraud_rule.py)...`, "agent-step");
            await delay(1000);
            
            appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] 🧠 Menganalisis korelasi log transaksi terhadap kode fraud_rule.py...`, "agent-step");
            await delay(1200);

            // Wait for backend API to finish
            const apiResp = await apiPromise;
            const apiRes = await apiResp.json();
            
            if (apiRes.status !== "ok") {
                throw new Error(apiRes.detail || "Investigasi API gagal.");
            }

            const report = apiRes.data;

            if (report.bug_detected) {
                appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] ❌ BUG TERDETEKSI: Aturan deteksi fraud salah dikonfigurasi!`, "agent-finding");
                appendConsoleLog(`   - File: fraud_rule.py`, "agent-finding");
                appendConsoleLog(`   - Kondisi "len(transactions) >= 3" memblokir user tanpa mengecek pola lompatan nominal.`, "agent-finding");
                await delay(1000);
                
                appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] 📄 Membuat berkas dokumen investigasi insiden PDF: ${report.report_id}.pdf...`, "agent-step");
                await delay(1000);
                
                appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] ✉️ Menyebarkan surel simulasi otomatis ke ${report.assigned_team}...`, "agent-step");
                await delay(1000);
                
                appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] ✅ Pengiriman simulasi berhasil. Tiket resmi di-RESOLVED!`, "agent-success");
            } else {
                appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] 🔍 Analisis Kode selesai. Tidak ada anomali atau bug terdeteksi di FRD App.`, "agent-step");
                appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] ⚠️ Masalah didelegasikan ke ${report.assigned_team} untuk pelacakan manual.`, "agent-finding");
                await delay(1000);
                
                appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] ✅ Laporan PDF selesai. Tiket resmi di-RESOLVED!`, "agent-success");
            }

            // Play successful beep sound or visual refresh
            investigatorStatusBadge.textContent = "STANDBY";
            investigatorStatusBadge.className = "badge standby";
            isInvestigating = false;

            // Reload all components
            loadDashboardData();

        } catch (err) {
            console.error(err);
            appendConsoleLog(`[${new Date().toLocaleTimeString("id-ID")}] 🚨 FATAL ERROR: Investigasi terhenti karena gangguan teknis: ${err.message}`, "agent-finding");
            investigatorStatusBadge.textContent = "STANDBY";
            investigatorStatusBadge.className = "badge standby";
            isInvestigating = false;
            loadDashboardData();
        }
    }

    // ==========================================
    // DETAIL REPORT MODAL VIEW
    // ==========================================

    async function openReportModal(reportId) {
        try {
            const resp = await fetch(`/api/reports/${reportId}`);
            const res = await resp.json();
            if (res.status === "ok") {
                const r = res.data;
                
                document.getElementById("md-report-id").textContent = r.report_id;
                document.getElementById("md-ticket-id").textContent = r.ticket_id;
                document.getElementById("md-user-id").textContent = r.user_id;
                
                const teamEl = document.getElementById("md-assigned-team");
                teamEl.textContent = r.assigned_team;
                teamEl.className = `badge ${r.bug_detected ? "danger" : "open"}`;

                document.getElementById("md-summary").textContent = r.summary;
                document.getElementById("md-root-cause").innerText = r.root_cause;
                
                // Format Code
                const codeBlock = document.getElementById("md-evidence-code");
                if (r.evidence_code && r.evidence_code.length > 0) {
                    codeBlock.innerText = r.evidence_code.join("\n");
                } else {
                    codeBlock.innerText = "// Tidak ada bukti kode khusus terlampir.";
                }

                // Format logs
                const logsContainer = document.getElementById("md-evidence-logs");
                logsContainer.innerHTML = "";
                if (r.evidence_logs && r.evidence_logs.length > 0) {
                    r.evidence_logs.forEach(logLine => {
                        const div = document.createElement("div");
                        div.className = "text-monospace py-1 border-bottom-1";
                        div.style.borderColor = "rgba(255,255,255,0.02)";
                        div.textContent = logLine;
                        logsContainer.appendChild(div);
                    });
                } else {
                    logsContainer.innerHTML = `<div class="text-muted p-2 text-center">Tidak ada log transaksi khusus terlampir.</div>`;
                }

                document.getElementById("md-recommendation").innerText = r.recommendation;

                // PDF Download Link
                btnDownloadPdf.href = `/api/reports/${r.report_id}/pdf`;

                // Show Modal
                reportModal.classList.add("active");
            }
        } catch (err) {
            alert("Gagal memuat detail laporan: " + err);
        }
    }

    // Modal Close Triggers
    const closeModal = () => reportModal.classList.remove("active");
    btnCloseModal.addEventListener("click", closeModal);
    btnCloseModalFooter.addEventListener("click", closeModal);
    window.addEventListener("click", (e) => {
        if (e.target === reportModal) closeModal();
    });

    // ==========================================
    // TAB: PLAYGROUND LOGIC
    // ==========================================

    async function loadPlaygroundTransactions() {
        try {
            const resp = await fetch("/api/playground/transactions");
            const res = await resp.json();
            if (res.status === "ok") {
                renderTransactionsTable(res.data);
            }
        } catch (err) {
            console.error(err);
        }
    }

    function renderTransactionsTable(txs) {
        if (!txs || txs.length === 0) {
            transactionsTableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Belum ada transaksi terekam.</td></tr>`;
            return;
        }

        transactionsTableBody.innerHTML = "";
        // Sort descending by ID
        txs.sort((a, b) => b.id - a.id);

        txs.forEach(tx => {
            const tr = document.createElement("tr");
            
            const statusBadge = tx.status === "blocked" 
                ? `<span class="badge blocked">BLOCKED</span>` 
                : `<span class="badge success">SUCCESS</span>`;

            tr.innerHTML = `
                <td><strong>TX-${tx.id.toString().padStart(3, "0")}</strong></td>
                <td><span class="badge bg-blue">${tx.user_id}</span></td>
                <td><strong>${formatIDR(tx.amount)}</strong></td>
                <td><span class="text-muted">${tx.to}</span></td>
                <td class="text-monospace text-muted" style="font-size: 11px;">${new Date(tx.timestamp).toLocaleString("id-ID")}</td>
                <td>${statusBadge}</td>
            `;
            transactionsTableBody.appendChild(tr);
        });
    }

    // Submit Playground Transfer Form
    playgroundTxForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const userId = document.getElementById("tx-user-id").value;
        const amount = document.getElementById("tx-amount").value;
        const to = document.getElementById("tx-to").value;

        try {
            const resp = await fetch(`/api/playground/transfer?user_id=${userId}&amount=${amount}&to=${to}`, {
                method: "POST"
            });
            const res = await resp.json();
            if (res.status === "ok") {
                // Show floating alerts/toasts or directly refresh
                alert(`Transaksi Diproses oleh Middleware!\nStatus Akhir: ${res.data.transaction.status.toUpperCase()}\nKeputusan Fraud: ${res.data.fraud_check.is_fraud ? "FRD BLOCKED!" : "AMAN"}`);
                loadPlaygroundData();
            }
        } catch (err) {
            alert("Gagal melakukan transfer: " + err);
        }
    });

    // ==========================================
    // TAB: EMAIL SIMULATOR LOGIC
    // ==========================================

    async function loadEmails() {
        try {
            const resp = await fetch("/api/emails");
            const res = await resp.json();
            if (res.status === "ok") {
                cachedEmails = res.data;
                renderEmailsList(cachedEmails);
            }
        } catch (err) {
            console.error(err);
        }
    }

    function renderEmailsList(emails) {
        if (!emails || emails.length === 0) {
            emailList.innerHTML = `<p class="text-center text-muted p-4">Belum ada email keluar yang disimulasikan oleh AI Agent.</p>`;
            emailPreviewEmpty.style.display = "flex";
            emailPreviewContent.style.display = "none";
            return;
        }

        emailList.innerHTML = "";
        // Sort descending by timestamp
        emails.sort((a, b) => b.timestamp.localeCompare(a.timestamp));

        emails.forEach(em => {
            const div = document.createElement("div");
            div.className = "email-item";
            div.setAttribute("data-email-id", em.email_id);
            
            const badgeTeam = em.to.includes("frd") 
                ? `<span class="badge blocked btn-sm">FRD Team</span>` 
                : `<span class="badge bg-blue btn-sm">Transfer Team</span>`;

            div.innerHTML = `
                <div class="email-item-header">
                    <span class="email-recipient">${em.to}</span>
                    <span class="email-time">${new Date(em.timestamp).toLocaleTimeString("id-ID")}</span>
                </div>
                <div class="email-subject">${em.subject}</div>
                <div class="email-item-header" style="margin-top: 6px;">
                    <span class="email-snippet">${em.body.replace(/\n/g, " ")}</span>
                    ${badgeTeam}
                </div>
            `;
            
            div.addEventListener("click", () => {
                // Remove selected classes
                document.querySelectorAll(".email-item").forEach(item => item.classList.remove("selected"));
                div.classList.add("selected");
                showEmailDetail(em.email_id);
            });

            emailList.appendChild(div);
        });
    }

    function showEmailDetail(emailId) {
        const em = cachedEmails.find(e => e.email_id === emailId);
        if (!em) return;

        emailPreviewEmpty.style.display = "none";
        emailPreviewContent.style.display = "block";

        emFrom.textContent = em.from;
        emTo.textContent = em.to;
        emSubject.textContent = em.subject;
        emDate.textContent = new Date(em.timestamp).toLocaleString("id-ID");
        emBody.textContent = em.body;
        
        emPdfName.textContent = em.pdf_filename;
        // Parse report ID out of pdf name (RPT-xxxxxxxxxxxxxx.pdf)
        const rptId = em.pdf_filename.replace(".pdf", "");
        emPdfLink.href = `/api/reports/${rptId}/pdf`;
    }

    // ==========================================
    // TAB: MICROSERVICES LOG VIEW LOGIC
    // ==========================================

    logTabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            logTabBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeLogApp = btn.getAttribute("data-app");
            loadLogsData();
        });
    });

    async function loadLogsData() {
        logTerminalTitle.textContent = `Raw Logs / Internal Data — ${activeLogApp.toUpperCase()} App`;
        logTerminalContent.innerHTML = `<p class="system-msg">[SYSTEM] Membuka koneksi data ke ${activeLogApp.toUpperCase()} App...</p>`;
        
        try {
            const resp = await fetch(`/api/microservices/logs/${activeLogApp}`);
            const res = await resp.json();
            
            if (res.status === "ok") {
                logTerminalContent.innerHTML = "";
                
                if (activeLogApp === "ticket") {
                    // Pre-format JSON
                    const dataStr = JSON.stringify(res.data, null, 2);
                    const pre = document.createElement("pre");
                    pre.className = "text-monospace text-green-glow";
                    pre.style.whiteSpace = "pre-wrap";
                    pre.textContent = dataStr;
                    logTerminalContent.appendChild(pre);
                } else if (activeLogApp === "transfer") {
                    const dataStr = JSON.stringify(res.data, null, 2);
                    const pre = document.createElement("pre");
                    pre.className = "text-monospace text-green-glow";
                    pre.style.whiteSpace = "pre-wrap";
                    pre.textContent = dataStr;
                    logTerminalContent.appendChild(pre);
                } else if (activeLogApp === "frd") {
                    // Output python code
                    const code = res.data.code || "# No code found";
                    const pre = document.createElement("pre");
                    pre.className = "text-monospace text-green-glow";
                    pre.style.whiteSpace = "pre-wrap";
                    pre.textContent = code;
                    logTerminalContent.appendChild(pre);
                } else if (activeLogApp === "middleware") {
                    // Output log file lines
                    const lines = res.data;
                    if (!lines || lines.length === 0) {
                        logTerminalContent.innerHTML = `<p class="system-msg">[SYSTEM] File log middleware.log masih kosong.</p>`;
                        return;
                    }
                    lines.forEach(line => {
                        const p = document.createElement("p");
                        p.className = "text-monospace text-green-glow py-1";
                        if (line.includes("ERROR")) p.className += " text-red";
                        else if (line.includes("BLOCKED")) p.className += " text-red";
                        else if (line.includes("START")) p.style.color = "#3b82f6";
                        p.textContent = line;
                        logTerminalContent.appendChild(p);
                    });
                }
                
                logTerminalContent.scrollTop = logTerminalContent.scrollHeight;
            }
        } catch (err) {
            logTerminalContent.innerHTML = `<p class="text-red">[SYSTEM] Gagal memuat data log: ${err.message}</p>`;
        }
    }


    // ==========================================
    // ORCHESTRATED TAB RELOADERS
    // ==========================================

    function loadDashboardData() {
        loadStats();
        loadTickets();
    }

    function loadPlaygroundData() {
        loadStats();
        loadPlaygroundTransactions();
    }

    function loadEmailsData() {
        loadEmails();
    }

    // Refresh Triggers
    document.getElementById("btn-refresh-tickets").addEventListener("click", loadTickets);
    document.getElementById("btn-refresh-tx").addEventListener("click", loadPlaygroundTransactions);
    document.getElementById("btn-refresh-emails").addEventListener("click", loadEmails);
    document.getElementById("btn-refresh-logs").addEventListener("click", loadLogsData);

    // Initial Dashboard Load
    loadDashboardData();
});
