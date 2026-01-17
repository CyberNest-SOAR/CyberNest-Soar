
# app/repository/feedback_repo.py

from pathlib import Path
import csv

FEEDBACK_FILE = Path("data/feedback.csv")

def save_feedback(case_id: str, subject: str, body: str, user_label: str, enrichment: dict):
    FEEDBACK_FILE.parent.mkdir(parents=True, exist_ok=True)
    file_exists = FEEDBACK_FILE.exists()

    with open(FEEDBACK_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow([
                "case_id","subject","body","user_label",
                "subject_len","text_len","num_urls","has_shortener",
                "num_exclamations","num_upper_words","num_suspicious_words","html_ratio","domains_in_text"
            ])
        writer.writerow([
            case_id, subject, body, user_label,
            enrichment.get("subject_len", 0),
            enrichment.get("text_len", 0),
            enrichment.get("num_urls", 0),
            int(bool(enrichment.get("has_shortener", False))),
            enrichment.get("num_exclamations", 0),
            enrichment.get("num_upper_words", 0),
            enrichment.get("num_suspicious_words", 0),
            enrichment.get("html_ratio", 0.0),
            "|".join(enrichment.get("domains_in_text", [])),
        ])
