# CerberOps: Complete Project Analysis

> Generated analysis of what CerberOps currently does, how it compares to the competition, and what to build next to stand out on GitHub.

---

## Part 1: What We Have Today

### Current Functionalities

| Feature | How It Works | User Experience |
|---------|-------------|-----------------|
| **Multi-Scanner Orchestration** | Coordinates Nmap, Nuclei, and OWASP ZAP in parallel via Celery background tasks | User toggles scanners on/off in the UI and hits "Launch Scan" |
| **Local AI Remediation** | Ollama generates Executive Summary + Technical Details + Remediation Plan from scan findings | Automatic — report appears in the dashboard when scan completes |
| **One-Command Install** | `./install.sh` detects OS, installs Docker/Ollama, picks AI model by RAM, runs `docker compose up` | User clones repo, runs one command, everything works |
| **Update Mode** | `./install.sh --update` upgrades Docker, Ollama, AI model weights, and Docker images | One command to stay current |
| **REST API** | FastAPI with Swagger docs at `/docs` — start scans, get results, download reports | CI/CD integration via `curl` or any HTTP client |
| **React Dashboard** | Dark-mode UI with health status cards, scan form, history sidebar, AI report tabs | Click-and-go web interface |
| **Async Processing** | Celery + Redis queue — scans run in background, don't block UI or API | User can launch multiple scans and come back later |
| **Hardened AI Prompts** | Temperature 0.1, OWASP mini-RAG context block, strict guardrails against hallucination | AI doesn't exaggerate severity or recommend deprecated headers |
| **Fallback Reports** | Template-based text reports when Ollama is unavailable | Users always get a report, even without AI |

### How Each Scanner Is Used

**Nmap (Network Discovery)**
- Checks: `which nmap` in PATH
- Runs: `asyncio.create_subprocess_exec("nmap", "-oX", ...)` 
- Parses: XML output → normalized Finding objects
- Finds: Open ports, running services, OS fingerprints

**Nuclei (Vulnerability Detection)**
- Checks: `which nuclei` in PATH
- Runs: `asyncio.create_subprocess_exec("nuclei", "-jsonl", ...)`
- Parses: JSON Lines → normalized Finding objects with CVEs
- Finds: Known CVEs, misconfigurations, exposed panels, outdated software

**OWASP ZAP (Web App Attack)**
- Connects: HTTP REST API to ZAP daemon at `http://zap:8080`
- Runs: Spider → Active Scan → Fetch Alerts
- Parses: JSON alerts → normalized Finding objects
- Finds: XSS, SQLi, CSRF, missing headers, insecure cookies

### Installation Flow

```
User clones repo
    └── ./install.sh
         ├── Detect OS (macOS/Linux/WSL2)
         ├── Docker installed? → No → Install it
         ├── Ollama installed? → No → Install it
         ├── Check RAM → Recommend model size
         ├── Pull AI model (600MB–5GB)
         ├── Create .env from template
         └── docker compose build && up -d
              ├── PostgreSQL (database)
              ├── Redis (task queue)
              ├── FastAPI API (backend)
              ├── Celery Worker (scan executor)
              ├── React Frontend (UI)
              ├── OWASP ZAP (web scanner)
              ├── Ollama (AI engine)
              └── Ollama-init (one-shot model pull)
```

### Data Flow: What Happens When You Click "Scan"

```
React UI → POST /api/v1/scan → FastAPI writes "pending" to Postgres
    → Dispatches Celery task to Redis queue
    → Worker picks up task, status → "running"
    → asyncio.gather(nmap_adapter, nuclei_adapter, zap_adapter)
    → Each adapter runs its tool, parses output → Finding objects
    → Deduplicate findings, save to Postgres
    → Status → "analyzing"
    → Format findings into text → Build prompt with OWASP context
    → POST to Ollama /api/generate (temperature=0.1, format=json)
    → Parse AI response → Save report to Postgres
    → Status → "completed"
    → React UI polls API → Shows report instantly
```

---

## Part 2: The Competitive Landscape (July 2026)

### Traditional Scanner Orchestrators

| Project | Stars | What It Does | AI? | Weakness |
|---------|-------|-------------|-----|----------|
| **reNgine** | ~8,700 | Full recon framework: subdomains, ports, vulns, screenshots | Yes (OpenAI/Ollama in v2.1+) | Cloud AI by default; complex Docker setup; dormant commits |
| **Osmedeus** | ~5,500 | YAML workflow engine with 80+ modules | No | CLI-only, no web UI, less maintained |
| **Sn1per** | ~10,200 | All-in-one bash pentest framework, 600+ exploits | No | 6GB Docker image; monolithic bash; no AI |
| **OWASP Nettacker** | ~3,500 | OWASP's official automated pentest framework | No | Basic web UI; narrow tool coverage |

### New AI-Powered Pentesting Tools (the real competition)

| Project | Stars | Key Innovation | Local AI? | Weakness for CerberOps to exploit |
|---------|-------|---------------|-----------|-----------------------------------|
| **PentestGPT** | ~14,800 | LLM-driven autonomous pentest agent (USENIX Security 2024 paper) | Ollama supported in legacy mode | Requires cloud API keys for full agent mode; no self-contained UI |
| **PentAGI** | ~21,000 | Fully autonomous multi-agent system with 20+ tools in Docker sandbox | No — requires OpenAI/Anthropic keys | **Cloud-only AI**; expensive per-run; no privacy guarantee |
| **Strix** | ~51,000 | Autonomous AI hackers that write and run real exploits with PoC validation | No — requires LLM API key (Claude/GPT) | **Cloud-only AI**; $0.35/scan with Claude; no offline mode |
| **Pentest Swarm AI** | ~2,200 | Multi-agent swarm with ReAct reasoning (Go + Claude) | No — Claude API required | Cloud-only; early stage |
| **PentestAgent** | ~2,900 | Black-box AI agent with MCP tool spawning and playbooks | No — requires API keys | Cloud-only; requires Tavily API for web search |
| **Dark-Moon** | ~830 | Privacy gateway tokenizes IPs before sending to cloud LLM | Partial — tokenization is local, but LLM is cloud | Still sends data to Claude; requires 32B+ model for local; complex setup |

### The Gap Nobody Has Filled

Here is what every single competitor either lacks or does poorly:

```
                        PentAGI   Strix   PentestGPT   reNgine   CerberOps
                        ───────   ─────   ──────────   ───────   ─────────
Fully local AI            ✗        ✗         ~           ~         ✓
Works offline             ✗        ✗         ~           ✗         ✓
One-command install       ~        ✓         ✗           ✗         ✓
AI drives scan strategy   ✗        ✓         ✓           ✗         ✗ ← BUILD THIS
AI validates findings     ✗        ✓         ✗           ✗         ✗ ← BUILD THIS
AI generates PoCs         ✗        ✓         ~           ✗         ✗ ← BUILD THIS
Chat with scan results    ✗        ✗         ~           ✗         ✗ ← BUILD THIS
Privacy guarantee         ✗        ✗         ✗           ✗         ✓
Developer-first UX        ✗        ✓         ✗           ~         ✓
Free (no API keys)        ✗        ✗         ✗           ~         ✓
```

**CerberOps is the only tool where:**
1. Everything runs 100% locally — no API keys, no cloud, no data leaks
2. It installs with one command on any OS
3. It's free forever (no $0.35/scan like Strix, no OpenAI bills like PentAGI)

**But it's missing the AI intelligence that makes Strix/PentAGI viral.** Those tools use AI to *drive* the scan, not just *summarize* it. That's what we need to build.

---

## Part 3: What To Build To Stand Out

### Priority 1: AI-Powered Smart Recon (Pre-Scan Intelligence)

**The problem:** Every scanner runs all checks against every target. Nuclei has 10,000+ templates. Running them all takes hours and generates noise.

**What to build:** Before scanning, do a 10-second fingerprint (HTTP headers, tech stack, ports). Feed it to Ollama. The AI picks which Nuclei tags, which ZAP scan policy, and which Nmap scripts to run.

```
User types: example.com
    → httpx fingerprint: WordPress 6.5, PHP 8.2, Nginx, Cloudflare
    → AI decides: "Run nuclei -tags wordpress,php,nginx,cloudflare"
    → Scan finishes in 2 minutes instead of 45 minutes
```

**Why it's killer:** No other local tool does this. Strix does it but requires Claude API ($). We do it with a 1.5GB local model for free.

### Priority 2: AI False Positive Filter (Zero-Noise Mode)

**The problem:** Nuclei and ZAP generate tons of false positives. A 403 page gets flagged as "Sensitive File Exposure." Security teams spend 80% of their time filtering garbage.

**What to build:** Before saving borderline findings (Low/Medium) to the database, pass the raw HTTP response to Ollama:

```
AI prompt: "The scanner flagged this URL as 'Exposed .git/config'. 
            Here is the HTTP response body: '<html>403 Forbidden</html>'.
            Is this a real git config leak or a WAF block page?"

AI response: "FALSE POSITIVE. The response is a generic 403 page, 
             not a git config file. Dropping finding."
```

**Why it's killer:** The Burp Suite Ollama extension (`burp-ollama`) does something similar but only for Burp users. The OASIS project has a "finding validation agent" concept. No orchestrator does this natively for Nuclei + ZAP output. We'd be the first open-source tool to ship built-in AI false positive elimination.

### Priority 3: Autonomous PoC Generator

**The problem:** Scanners say "Possible SQL Injection" but developers can't verify it. They don't know if it's real.

**What to build:** When a High/Critical finding is detected, capture the exact HTTP request. Ask Ollama to write a safe Python script or `curl` command that reproduces the vulnerability:

```
AI prompt: "Nuclei found SQL injection at https://example.com/search?q=test.
            Template: CVE-2023-XXXX. HTTP request: GET /search?q=test'--
            Write a safe Python script using requests to verify this."

AI output: 
    import requests
    r = requests.get("https://example.com/search", 
                     params={"q": "test' OR '1'='1"})
    if "mysql" in r.text.lower() or r.status_code == 500:
        print("[CONFIRMED] SQL Injection — error-based")
```

**Why it's killer:** Strix (51K stars) went viral precisely because of PoC validation. But Strix requires cloud AI. We do it locally, privately, for free. This single feature would drive GitHub stars.

### Priority 4: "Chat With Your Scan" (Conversational Security)

**The problem:** Looking through tables of 200 vulnerabilities is overwhelming. Developers want to ask questions.

**What to build:** Add a chat panel in the React UI. Load the scan findings into Ollama's context window. Let users ask natural language questions:

```
User: "Did you find any databases exposed?"
AI:   "Yes. Nmap found Redis on port 6379 without authentication on 
       host 10.0.0.5. This is CRITICAL — run: 
       redis-cli -h 10.0.0.5 CONFIG SET requirepass 'your-password'"

User: "What's the most urgent thing to fix?"
AI:   "The open Redis instance. An attacker can read all cached data, 
       execute commands via EVAL, and potentially gain RCE. Fix it now."

User: "Generate a security report for my manager"
AI:   [generates executive summary in plain English]
```

**Why it's killer:** Nobody has this. Not PentAGI, not Strix, not reNgine. It makes CerberOps accessible to junior developers who don't understand CVE codes. The closest thing is Burp-Ollama's "Ask Ollama" feature, but that's inside Burp Suite (paid tool), not a free web UI.

### Priority 5: ProjectDiscovery Fast Tools Integration

**The problem:** Nmap is slow. ZAP's spider misses JavaScript-rendered pages. We're missing subdomain discovery entirely.

**What to integrate:**

| Tool | What It Does | Speed vs Current |
|------|-------------|-----------------|
| **Subfinder** | Passive subdomain enumeration (crt.sh, APIs) | New capability |
| **httpx** | HTTP probing + tech fingerprinting | Instant fingerprinting for AI Smart Recon |
| **Naabu** | TCP port scanning (Go/Rust, SYN scan) | 10x faster than Nmap for port discovery |
| **Katana** | JavaScript-aware web crawling | Catches SPA endpoints ZAP misses |

These feed into the AI Smart Recon pipeline: `Subfinder → Naabu → httpx → AI decides what to scan → Nuclei/ZAP`.

---

## Part 4: Why CerberOps Will Win

### The Positioning

```
 ┌──────────────────────────────────────────────────────┐
 │          WHERE CERBEROPS FITS IN THE MARKET          │
 │                                                      │
 │   Strix / PentAGI                                    │
 │   ┌─────────────┐     CerberOps (with new AI)       │
 │   │ Smart AI    │     ┌─────────────┐                │
 │   │ PoC Exploit │     │ Smart AI    │                │
 │   │ Cloud-Only  │     │ PoC Exploit │                │
 │   │ Paid API    │     │ 100% LOCAL  │                │
 │   │ $0.35/scan  │     │ FREE        │                │
 │   └─────────────┘     │ PRIVATE     │                │
 │                       │ OFFLINE     │                │
 │   reNgine / Sn1per    │ One-Click   │                │
 │   ┌─────────────┐     └─────────────┘                │
 │   │ Dumb tools  │                                    │
 │   │ No AI       │                                    │
 │   │ Raw output  │                                    │
 │   │ Complex     │                                    │
 │   └─────────────┘                                    │
 └──────────────────────────────────────────────────────┘
```

### The Tagline

> **"The AI security engineer that never phones home."**

CerberOps is the **only** tool that combines autonomous AI-driven scanning (like Strix) with complete local privacy (unlike everyone else). No API keys. No cloud bills. No data leaks. One command to install. Free forever.

### What Makes Users Star a Repo

Based on what made Strix (51K), PentAGI (21K), and PentestGPT (15K) go viral:

1. **"It actually works in 5 minutes"** — We already have this (install.sh)
2. **"The AI does something I can't"** — We need Smart Recon + PoC Generator
3. **"I can show this to my boss"** — We need Chat With Your Scan + polished reports
4. **"It respects my privacy"** — We already have this (100% local)
5. **"It's free"** — We already have this (no API keys needed)

### Suggested Build Order

| Order | Feature | Effort | Impact | Why This Order |
|-------|---------|--------|--------|----------------|
| 1 | AI False Positive Filter | Medium | High | Immediate quality improvement; every scan gets better |
| 2 | AI Smart Recon | Medium | Very High | Scans go from 45 min to 2 min; visible wow factor |
| 3 | PoC Generator | Medium | Viral | This is the #1 reason Strix got 51K stars |
| 4 | Chat With Your Scan | Medium | High | Makes CerberOps accessible to non-security people |
| 5 | ProjectDiscovery Tools | Large | Medium | Expands attack surface coverage; more professional |

---

## Part 5: Tools & Projects We Should Study or Integrate

| Project | What to Take From It |
|---------|---------------------|
| **OASIS** (`psyray/oasis`) | Their "Finding Validation Agent" concept — deterministic code checks before LLM narrative |
| **Burp-Ollama** (`jayluxferro/burp-ollama`) | Their "Validate False Positive" prompt design for scanner findings |
| **PATCHY** (`copyleftdev/patchy`) | MCP server wrapping ProjectDiscovery tools — we could adopt similar adapter patterns |
| **Citadel-Local** (`joeynyc/Citadel-Local`) | Multi-model pipeline: fast model for triage, big model for deep analysis |
| **Dark-Moon** | Privacy Gateway tokenization concept — could enhance our "no data leaves" story |
| **Attack-Surface-Management** (`Krishcalin`) | Pure-Python fallbacks for Go tools — works without Go installed |

---

*This document is for internal planning. Delete before public release or move to `docs/internal/`.*
