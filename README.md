# 🛡️ SOAR Phishing Detection MVP

A minimal **Security Orchestration, Automation, and Response (SOAR)** system focusing on **phishing email detection**.
This MVP demonstrates how backend automation, AI checks, and database orchestration can work together in a cybersecurity use case.



## 🚀 Project Overview

This MVP simulates a small SOAR pipeline that:

1. Receives an email via API.
2. Parses and extracts key fields (sender, recipients, subject, body, URLs, etc.).
3. Stores email data in **Cassandra**.
4. Runs a lightweight **AI model** to check for suspicious features (starting with spelling analysis).
5. Returns a JSON response with the classification result.



## 🧩 Architecture

```
User → FastAPI Backend → Cassandra Database + AI Model → JSON Response
```

### Components

* **FastAPI (Backend):** Receives emails and manages API endpoints.
* **Cassandra (Database):** Stores parsed email data and model results.
* **AI Model:** Performs a spelling-based phishing suspicion check.
* **React Frontend (Later):** Simple dashboard for viewing analysis results.

---

## 🏗️ Folder Structure

```
soar-sut/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── ai/
│   │   ├── api/
│   │   ├── config/
│   │   ├── services/
│   │   ├── core/
│   │   ├── models/
│   │   └── repository/
│   ├── .dockerignore  
│   ├── Dockerfile
│   └── requirements.txt
│
├── data/
│   └── datasets/ (for training/testing)
│
├── infra/
│   └── docker-compose.yml (coming soon)
│
└── README.md
```



## 🧮 Tech Stack

| Component        | Technology                                        |
| ---------------- | ------------------------------------------------- |
| Backend          | FastAPI                                           |
| Database         | Apache Cassandra                                  |
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

Create a `.env` file inside `backend/` with:

```
CASSANDRA_HOST=127.0.0.1
CASSANDRA_KEYSPACE=soar_db
```

### 5. Run the FastAPI App

```bash
uvicorn app.main:app --reload
```

Then visit:
👉 [http://localhost:8000/docs](http://localhost:8000/docs)



## 🧠 API Example

### POST `/api/submit_email`

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
  "record_id": "12345",
  "spelling_score": 0.72,
  "model_label": "suspicious"
}
```

---

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
