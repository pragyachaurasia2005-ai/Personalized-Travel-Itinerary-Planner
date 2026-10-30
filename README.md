# 🌍 TravelCraft AI — Personalized Travel Itinerary Planner

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.x-61DAFB.svg?logo=react)](https://react.dev/)
[![TailwindCSS](https://img.shields.io/badge/Tailwind-3.x-38B2AC.svg?logo=tailwind-css)](https://tailwindcss.com/)
[![Google Gemini](https://img.shields.io/badge/AI-Google%20Gemini%202.5%2F3.5%20Flash-4285F4.svg?logo=google)](https://aistudio.google.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **A full-stack, AI-powered travel planning platform designed to synthesize highly personalized, day-by-day travel itineraries based on real-time constraints, travel personas, budgets, and multi-currency calculations.**

---

## 📑 Table of Contents

1. [Project Introduction](#-project-introduction)
2. [Project Objectives](#-project-objectives)
3. [Key Features](#-key-features)
4. [Technologies Used](#-technologies-used)
5. [System Architecture](#-system-architecture)
6. [System Requirements](#-system-requirements)
7. [Installation & Setup](#-installation--setup)
8. [Configuration Guide (Gemini & Supabase)](#-configuration-guide-gemini--supabase)
9. [Running the Application](#-running-the-application)
10. [Running Automated Tests](#-running-automated-tests)
11. [Deployment Configuration (Render)](#-deployment-configuration-render)
12. [Project Directory Structure](#-project-directory-structure)
13. [Security & Privacy](#-security--privacy)

---

## 🌟 Project Introduction

Traditional travel planning is fragmented, time-consuming, and mentally fatiguing. Travelers frequently spend hours juggling multiple websites, reviews, maps, and currency exchange tables, only to end up with inflexible or generic itineraries that do not reflect their budget or pacing.

**TravelCraft AI** bridges this gap by combining **Google Gemini Generative AI** with structured heuristic constraint-satisfaction algorithms. Built as a unified modern web application (React frontend + FastAPI backend + Supabase/SQLite dual database), it generates day-by-day itineraries complete with morning, afternoon, and evening activities, transit logistics, itemized expense breakdowns, packing checklists, and local etiquette recommendations.

If external AI services are unavailable or unconfigured, the application seamlessly activates an **Adaptive Local Engine** to guarantee 100% uptime with zero artificial responses.

---

## 🎯 Project Objectives

- **Intelligent Automation**: Reduce itinerary preparation time from hours to seconds while maintaining high personalization for any destination worldwide.
- **Persona-Driven Customization**: Tailor pacing, activity intensity, and dining choices to specific travel personas (Solo, Couple, Family, Friends, Business).
- **Multi-Currency Budget Integrity**: Provide strict mathematical consistency in itemized expenses across global currencies including **INR (₹)**, **USD ($)**, **EUR (€)**, **GBP (£)**, and **JPY (¥)**.
- **Zero-Repetition Scheduling**: Guarantee that generated activities are completely distinct across every day of the itinerary.
- **Fault-Tolerant Dual-Tier Architecture**: Cloud-first persistence using **Supabase PostgreSQL** with an automatic offline fallback to **local SQLite**.
- **Privacy & Key Security**: Strict backend-only handling of all API keys, ensuring no sensitive credentials leak into client-side code.

---

## 🚀 Key Features

### 1. 🤖 Google Gemini AI & Adaptive Local Engine
- **Direct Gemini API Integration**: Integrated with Google's latest `google-genai` SDK using structured JSON schema output generation.
- **Dynamic Model Cascade**: Automatically coordinates across `gemini-2.5-flash`, `gemini-3.5-flash`, `gemini-3.8-flash`, and `gemini-flash-latest` to gracefully handle deprecations, regional rollouts, or transient 503 load spikes.
- **Adaptive Fallback Engine**: If no API key is provided or the network is offline, the local adaptive engine constructs complete, realistic itineraries for any destination without downtime.
- **Truthful Status Reporting**: The navigation bar and itinerary headers transparently display whether the plan was synthesized by **Google Gemini** or the **Adaptive Local Engine**.

### 2. 💱 Multi-Currency Financial Engine
- Direct support for **INR (₹)**, **USD ($)**, **EUR (€)**, **GBP (£)**, **JPY (¥)**, **CAD (C$)**, and **AUD (A$)**.
- Strict mathematical integrity: 
  $$\text{Total} = \text{Stay} + \text{Dining} + \text{Attractions} + \text{Transit} + \text{Misc}$$
  $$\text{Per Person} = \frac{\text{Total}}{\text{Group Size}}$$
- Every activity card displays converted local estimates aligned with the trip currency.

### 3. ☁️ Supabase Cloud & SQLite Dual Storage
- **Cloud Database**: Persists trips to **Supabase PostgreSQL** with instant synchronization when credentials are configured.
- **Offline SQLite**: Zero-configuration local database (`travel_planner.db`) used as primary when Supabase is unconfigured, or as an automatic offline backup.
- **Full CRUD Capabilities**: Users can view, edit trip titles, modify individual activity timings and descriptions, regenerate single days, and delete trips.

### 4. 🗓️ Exact Date Matching & Zero Repetition
- Calculates exact day counts and dates from `start_date` to `end_date` (e.g., Dec 1 to Dec 5 = exactly 5 days).
- Guarantees zero activity repetition across days using unique spatial-heuristic generation.
- **Single-Day AI Re-roll**: Regenerate any specific day (e.g., "Day 2: Focus on street food and museums") without altering the rest of the trip.

### 5. 🎯 Pre-Built Evaluation Scenarios
- **Scenario 1 (Solo Weekend Getaway)**: Fast-paced discovery for solo explorers optimizing sights and affordable dining.
- **Scenario 2 (Couple Vacation)**: Relaxed, romantic pacing with curated dining, scenic spots, and boutique stays.
- **Scenario 3 (Small Group Holiday)**: Balanced group logistics, adventure activities, and shared budget tracking.

### 6. 📄 Markdown & Print Export
- One-click export of the complete itinerary into clean GitHub Flavored Markdown formatted with local currency symbols for offline printing or sharing.

---

## 🛠️ Technologies Used

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | React 18 | Dynamic SPA reactive UI components |
| **Frontend Styling** | Tailwind CSS 3.x (CDN) | Responsive SaaS dashboard styling |
| **Icons** | Lucide Icons | Clean modern iconography |
| **Backend** | Python 3.10+ & FastAPI | High-performance asynchronous REST API |
| **ASGI Server** | Uvicorn | High-throughput web server |
| **Data Validation** | Pydantic v2 | Strict schema validation and typing |
| **AI Integration** | Google GenAI SDK (`google-genai`) | Gemini structured content generation |
| **Cloud Storage** | Supabase (`supabase-py`) | Cloud PostgreSQL persistence |
| **Local Storage** | SQLite3 | Embedded zero-dependency SQL persistence |
| **Environment** | `python-dotenv` | Secure environment variable management |
| **Testing** | Pytest & HTTPX | Automated endpoint and scenario validation |

---

## 💻 System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu, Debian, Fedora, etc.)
- **Python**: Version **3.10**, **3.11**, **3.12**, or **3.13** installed.
- **Web Browser**: Any modern browser (Google Chrome, Mozilla Firefox, Microsoft Edge, Safari).
- **Internet Connection**: Required for Google Gemini API and Supabase Cloud. *(Not required for the local adaptive engine + SQLite).*

---

## 📦 Installation & Setup

### 1. Clone or Extract the Repository
```bash
git clone https://github.com/your-username/travel-itinerary-planner.git
cd travel-itinerary-planner
```

### 2. Create a Virtual Environment (Recommended)
**On Windows:**
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Required Dependencies
```bash
pip install -r requirements.txt
```

---

## ⚙️ Configuration Guide (Gemini & Supabase)

All sensitive secrets are read from the project root `.env` file and are **never exposed to the frontend or committed to GitHub**.

### Step 1: Create your `.env` file
Copy the provided template:
```bash
# On Windows PowerShell:
Copy-Item .env.example .env

# On macOS / Linux / Bash:
cp .env.example .env
```

### Step 2: Configure Google Gemini API (Optional, Recommended)
1. Visit [Google AI Studio](https://aistudio.google.com/) and sign in with your Google account.
2. Click **Get API key** and generate a free API key.
3. Open `.env` and paste your key:
   ```env
   GEMINI_API_KEY=your_actual_gemini_api_key_here
   GEMINI_MODEL=gemini-2.5-flash
   ```

> [!NOTE]
> If `GEMINI_API_KEY` is left blank, the application will automatically run using its built-in **Adaptive Local Engine**.

### Step 3: Configure Supabase Cloud Database (Optional)
1. Create a free account at [Supabase](https://supabase.com/).
2. Create a new project and navigate to the **SQL Editor**.
3. Copy and run the contents of [`backend/supabase_schema.sql`](backend/supabase_schema.sql).
4. Go to **Project Settings** > **API** to copy your **Project URL** and **anon public key**.
5. Add them to `.env`:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   ```

> [!NOTE]
> If Supabase credentials are not set, the platform automatically stores all trips locally in SQLite (`travel_planner.db`).

---

## ▶️ Running the Application

### Option A: One-Click Launcher (Recommended)
Run the automated runner which starts the FastAPI backend and automatically opens the user interface in your default browser:
```bash
python run.py
```
- **Web Application**: [`http://127.0.0.1:8000`](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [`http://127.0.0.1:8000/docs`](http://127.0.0.1:8000/docs)
- **Alternative ReDoc Docs**: [`http://127.0.0.1:8000/redoc`](http://127.0.0.1:8000/redoc)

### Option B: Direct Uvicorn Launch
```bash
uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 🧪 Running Automated Tests

The project includes both a standard `pytest` suite and a comprehensive 9-module verification script that tests real-world scenarios, currency conversion, date consistency, and budget accuracy.

### Run Standard Pytest Suite
```bash
pytest backend/tests/test_api.py -v
```

### Run Comprehensive 9-Point Verification Suite
```bash
python backend/tests/run_tests.py
```
This suite automatically verifies:
1. System Health & Truthful Status Indicators
2. Multi-Currency calculations (INR, USD, EUR, JPY)
3. Exact Date Range & Duration Consistency
4. Zero Activity Repetition Across Days
5. Strict Mathematical Budget Integrity
6. Trip Saving, Updating, and Retrieval (CRUD)
7. AI Single-Day Regeneration
8. Markdown Export Functionality
9. Trip Deletion

---

## ☁️ Deployment Configuration (Render)

This repository includes pre-configured deployment files ready for 1-click deployment on [Render.com](https://render.com/):

- [`render.yaml`](render.yaml) — Declarative Infrastructure-as-Code blueprint.
- [`Procfile`](Procfile) — Production web process entrypoint.

### Steps to Deploy on Render:
1. Push your repository to GitHub.
2. Sign in to [Render Dashboard](https://dashboard.render.com/) and click **New +** > **Blueprint**.
3. Connect your repository. Render will automatically detect `render.yaml`.
4. In the Render environment variable settings, set:
   - `GEMINI_API_KEY`: Your Gemini API key.
   - `SUPABASE_URL`: (Optional) Your Supabase project URL.
   - `SUPABASE_KEY`: (Optional) Your Supabase anon key.
5. Click **Apply**. Render will install dependencies and launch the live web application with a public HTTPS URL.

---

## 📁 Project Directory Structure

```
travel-itinerary-planner/
├── .env.example             # Safe template for environment variables
├── .gitignore               # Excludes secrets, databases, caches, and node_modules
├── Procfile                 # Production process file for PaaS deployments
├── README.md                # Comprehensive documentation and project guide
├── render.yaml              # Render cloud deployment blueprint
├── requirements.txt         # Pinned Python package dependencies
├── run.py                   # Automated server launch script with browser auto-open
│
├── backend/
│   ├── supabase_schema.sql  # SQL DDL for Supabase cloud database setup
│   ├── app/
│   │   ├── __init__.py      # Package initializer
│   │   ├── ai_engine.py     # Gemini generative AI & adaptive local fallback engine
│   │   ├── config.py        # Centralized settings & currency conversion rates
│   │   ├── export_utils.py  # Markdown export generator with currency formatting
│   │   ├── main.py          # FastAPI application, routing, and static file serving
│   │   ├── models.py        # Pydantic data models & request/response schemas
│   │   ├── preset_scenarios.py # Scenarios (Solo Weekend, Couple Vacation, Group Holiday)
│   │   ├── storage.py       # Dual-storage manager (Supabase Cloud + SQLite fallback)
│   │   └── supabase_service.py # Supabase client management & connection health
│   │
│   └── tests/
│       ├── run_tests.py     # 9-module comprehensive verification suite
│       └── test_api.py      # Automated pytest unit and integration tests
│
└── frontend/
    ├── app.js               # React 18 single-page application with modern state management
    ├── index.html           # HTML5 container with Tailwind CSS, Lucide icons, and Babel
    └── styles.css           # Custom animations, transitions, and scrollbar styling
```

---

## 🔒 Security & Privacy

- **No Secrets in Code**: All API keys and connection strings are strictly managed via environment variables.
- **Frontend Isolation**: No API keys are ever transmitted to or stored in client-side React code.
- **Git Exclusions**: The provided [`.gitignore`](.gitignore) automatically prevents `.env`, `*.db`, `__pycache__`, `.venv`, and temporary log files from being accidentally committed to GitHub.

---

## 🎓 Academic Submission Details

- **Project Title**: Personalized Travel Itinerary Planner (TravelCraft AI)
- **Domain**: Artificial Intelligence / Full-Stack Web Development
- **Architecture**: Decoupled Client-Server (SPA React Frontend + RESTful FastAPI Backend)
- **Evaluation Highlights**:
  - Live Gemini API integration with zero-downtime adaptive local engine fallback.
  - Multi-currency financial engine supporting INR (₹) and global currencies with strict sum verification.
  - Non-repeating day-by-day scheduling with single-day regeneration capabilities.
  - Truthful status indicators distinguishing real AI and cloud persistence from local fallbacks.
