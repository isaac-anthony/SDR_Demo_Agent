# Brine-Engine-V2: Autonomous SDR Agent 🚀

Brine-Engine-V2 is an end-to-end, autonomous lead generation and outreach pipeline designed for modern SDR workflows. It replaces manual prospecting with an intelligent, self-healing system that discovers high-intent leads, enriches them with deep website context, and drips personalized outreach via the Gmail API.

---

## 🛠 Core Features

### 1. **Discovery (Phase 1)**
Uses **Stealth Playwright** to perform local visual scraping of Google Maps. It identifies businesses in target niches and cities, extracting names, websites, and review data without being blocked.

### 2. **Enrichment & AI Hook Generation (Phase 2)**
Crawls business websites locally to extract "Golden Nuggets" (Founder names, specific awards, niche services). It uses **GPT-4o** to:
- **Score leads (1-10)** based on automation potential.
- **Generate hyper-personalized hooks** that prove a human actually visited the site.
- **Find verified emails** and social handles.

### 3. **Smart Sync & Delivery (Phase 3)**
Automatically upserts leads into a **Google Sheet**. It performs "Update-on-Match" logic via website URL to ensure your database is always deduplicated and up-to-date.

### 4. **Autonomous Outreach (Phase 4)**
A drip-campaign engine integrated with **Gmail API (OAuth)**. 
- **A/B Testing**: Rotates between "Deal-First," "AI Employee," and "Niche Growth" templates.
- **Human Mimicry**: Randomized delays (~10 mins) between sends.
- **Test Mode**: Includes a `--test-email` flag to route all outreach to your own inbox for review.

### 5. **Self-Healing Watchdog**
The `guard_dog.py` monitor ensures the engine runs 24/7. If a process crashes or hangs, the watchdog automatically restarts it from the last saved state.

---

## 🏗 Tech Stack
- **Languages**: Python 3.10+
- **Automation**: Playwright (Stealth), Gmail API, Google Sheets API
- **Intelligence**: OpenAI GPT-4o
- **State Management**: Local JSON persistence for autonomous recovery

---

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/isaac-anthony/SDR_Demo_Agent.git
cd SDR_Demo_Agent

# Install dependencies
python3 -m pip install -r requirements.txt
python3 -m playwright install
```

### 2. Configuration
Create a `.env` file based on `.env.example`:
```ini
OPENAI_API_KEY=your_key_here
GOOGLE_SHEETS_ID=your_sheet_id
SMTP_USER=your_gmail@gmail.com
# Google Cloud credentials (client_secrets.json) are required for API access
```

### 3. Usage

**Run a specific batch (Test Mode):**
```bash
python3 main.py --limit 5 --city "San Diego, CA" --niche "Pool Cleaning" --test-email "your-inbox@gmail.com"
```

**Launch Autonomous Mode (The "Set It & Forget It" Command):**
```bash
python3 guard_dog.py --limit 50 --city "Austin, TX" --niche "HVAC"
```

---

## 📁 Project Structure
- `main.py`: The central orchestrator.
- `guard_dog.py`: Watchdog process for 24/7 autonomous operation.
- `execution/`:
    - `scrape_directory_local.py`: Google Maps visual agent.
    - `scrape_website_context.py`: AI enrichment & hook engine.
    - `outreach_campaign.py`: Gmail API drip sender.
    - `sync_to_sheet.py`: Google Sheets upsert logic.
- `directives/`: SOPs and Master Directives for the AI agents.

---

## 🛡 Security & Privacy
This repository includes a `.gitignore` that protects:
- API Keys (`.env`)
- OAuth Tokens (`token.json`)
- Google Cloud Secrets (`client_secrets.json`)
- Local Scratchpads (`.tmp/`)

---
**Developed by [Isaac Gutierrez](https://github.com/isaac-anthony) | Brine.ai**
