# 🛡️ SOAR Phishing Detection MVP

A minimal **Security Orchestration, Automation, and Response (SOAR)** system focusing on **phishing email detection**.
This MVP demonstrates how backend automation, AI checks, and database orchestration can work together in a cybersecurity use case.



## 🚀 Project Overview

This MVP simulates a small SOAR pipeline that:

1. Receives an email via API.
2. Parses and extracts key fields (sender, recipients, subject, body, URLs, etc.).
3. Stores email data in **Postgres**.
4. Runs a lightweight **AI model** to check for suspicious features (starting with spelling analysis).
5. Returns a JSON response with the classification result.



## 🧩 Architecture

```
User → FastAPI Backend → Postgres Database + AI Model → JSON Response
```

### Components

* **FastAPI (Backend):** Receives emails and manages API endpoints.
* **PostgreSQL (Database):** Stores parsed email data and model results.
* **AI Model:** Performs a spelling-based phishing suspicion check.
* **React Frontend (Later):** Simple dashboard for viewing analysis results.

---

## 🏗️ Folder Structure

```
soar/
├── backend/
│   └── app/
│       ├── ai/
│       ├── client/
│       ├── config/
│       ├── controllers/
│       ├── core/
│       ├── models/
│       ├── repository/
│       └── services/
├── data/
│   └── data.csv
├── infra/
│   └── docker-compose.yml
└── README.md
```



## 🧮 Tech Stack

| Component        | Technology                                        |
| ---------------- | ------------------------------------------------- |
| Backend          | FastAPI                                           |
| Database         | PostgreSQL                                        |
| AI Model         | Python (TextBlob / PySpellChecker / Scikit-learn) |
| Frontend         | React (coming soon)                               |
| Containerization | Docker / Docker Compose                           |



## ⚙️ Setup & Run Locally

### 1. Clone the Repository

```bash
git clone https://github.com/Momen959/soar-sut.git
cd soar-sut/backend
```

### 2. Create a Virtual Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Copy `backend/env.example` to `backend/.env` and adjust values as needed:

```
cp backend/env.example backend/.env
```

### 5. Run the FastAPI App

```bash
uvicorn app.main:app --reload
```

Then visit:
👉 [http://localhost:8000/docs](http://localhost:8000/docs)



## 🧠 API Example

### Environment Variables

The backend reads configuration via environment variables (loaded from `backend/.env`). The sample file contains:

- `DATABASE_URL`: PostgreSQL connection string.
- `GOOGLE_CLIENT_SECRET_FILE`: path to your OAuth client JSON.
- `GMAIL_SYNC_FOLDER`: Gmail label to sync.
- `GOOGLE_TOKEN_DIR`: directory for cached OAuth tokens.
- `MODEL_ARTIFACT_PATH`: persisted phishing model file (optional).
- `VECTORIZER_ARTIFACT_PATH`: persisted TF-IDF vectorizer file (optional).
- `TRAINING_DATA_PATH`: CSV used when re-training the phishing model.

### POST `/api/emails`

#### Request

```json
{
  "sender": "test@example.com",
  "recipients": ["user@domain.com"],
  "subject": "Win a prize now",
  "body": "Click here to claim your prize",
  "attachments": []
}
```

#### Response

```json
{
  "record_id": 1,
  "gmail_id": "manual-2a1e75c98a2247f584e41a5303b0f3c7",
  "analysis": {
    "spelling_score": 0.31,
    "keyword_score": 0.08,
    "composite_score": 0.196,
    "model_label": "suspicious"
  }
}
```

### POST `/api/emails/sync`

Synchronise the configured Gmail inbox with the API. Each message is normalised, analysed, and stored (or updated) in PostgreSQL. Optional `max_results` query parameter lets you cap the batch size.

### GET `/api/emails`

Fetch analysed emails with pagination via `limit` and `offset` query parameters.

### GET `/api/emails/{gmail_id}`

Retrieve a single analysed email by its Gmail ID (or the auto-generated manual ID).

### Training the ML model (optional)

The system ships with a heuristic detector by default. To activate the ML-based classifier, place your dataset at `TRAINING_DATA_PATH` and run a one-off training step (for example via an interactive shell):

```python
from pathlib import Path
from app.ai.phishing_model import PhishingDetector

detector = PhishingDetector(
    model_path=Path("artifacts/phishing_model.joblib"),
    vectorizer_path=Path("artifacts/phishing_vectorizer.joblib"),
)
detector.train(Path("data/data.csv"))
```

After training, the API automatically loads the persisted artifacts.

---

## 📝 Logging and Accessing Logs

The backend configures a centralized logger which writes to both the console
and a rotating file under `backend/logs/soar.log` (5MB per file, 3 backups).


How to view logs locally

1. Tail the log file:

```bash
tail -f backend/logs/soar.log
```

2. Show the last N lines:

```bash
tail -n 200 backend/logs/soar.log
```

When running with Docker / Docker Compose

```bash
docker compose logs -f backend
```

If you run `uvicorn` directly the console will contain the same log messages.

Notes

  issues), logging falls back to console only and a warning appears on startup.
 You can adjust log level by changing `app/config/logging_config.py` or setting an
  environment variable in your deployment/docker-compose to control verbosity.


## 👥 Team

| Name       | Role                        |
| ---------- | --------------------------- |
| **Hanaa**  | Project Leader (Security)   |
| **Paula**  | Security Team Leader        |
| **Amir**   | Security Team Member        |
| **Ahmed**  | Security Team Member        |
| **Momen**  | AI Team Leader              |
| **Pavlly** | Database Engineer           |
| **Nayra**  | AI Model Developer          |
| **Steven** | Backend Developer           |
| **Habiba** | Frontend Developer          |



## 📟 License

This project is for **educational purposes** as part of the SOAR Project 1 at SUT.
Feel free to use or adapt it for learning or non-commercial purposes.



## 🛏️ Future Work

* Integrate multiple SOAR use cases (DDoS, Brute Force, Malware)
* Add alert correlation and automated responses
* Build frontend dashboard for real-time monitoring
* Containerize using Docker Compose
