"""ML-backed phishing detection.

This module implements a persisted Scikit-learn detector which loads a
serialized RandomForest model and TF-IDF vectorizer from disk. The file
paths are supplied by the caller and are logged during load attempts to
make failures easy to diagnose.

Notes for readers:
- The detector will raise a `RuntimeError` from `analyse()` when artifacts
    are missing or failed to load. The calling code should catch this and
    decide whether to fallback to heuristics or return a service error.
"""


from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, Optional
import logging

import joblib
import numpy as np  # NEW
import scipy.sparse as sp  # NEW
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
# from spellchecker import SpellChecker  # (غير مستخدم) ممكن تتشال لو مش بتستخدميها

from app.services.enrichment_service import enrichment_features  # NEW

log = logging.getLogger(__name__)


class SklearnDetector:
    """RandomForest-based phishing classifier persisted to disk."""

    def __init__(
        self,
        model_path: Path,
        vectorizer_path: Path,
        threshold: float = 0.5,
    ):
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.threshold = threshold
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.model: Optional[RandomForestClassifier] = None
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        # Log paths being attempted to help with troubleshooting
        log.debug("SklearnDetector loading artifacts, model_path=%s, vectorizer_path=%s",
                  self.model_path, self.vectorizer_path)

        if self.model_path.exists() and self.vectorizer_path.exists():
            try:
                self.model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                log.info("Loaded sklearn artifacts from disk")
            except Exception:
                log.exception("Failed to load sklearn artifacts; disabling ML detector")
                self.model = None
                self.vectorizer = None
        else:
            log.warning(
                "Sklearn artifacts not found (model_exists=%s, vectorizer_exists=%s)",
                self.model_path.exists(),
                self.vectorizer_path.exists(),
            )
            self.model = None
            self.vectorizer = None

    def is_ready(self) -> bool:
        return self.model is not None and self.vectorizer is not None

    # NEW: تحويل الـ enrichment لمتجه رقمي ثابت الترتيب
    @staticmethod
    def _enrichment_vector(subject: str, body: str) -> np.ndarray:
        feats = enrichment_features(subject, body)
        return np.array([
            feats["subject_len"],        # 0
            feats["text_len"],           # 1
            feats["num_urls"],           # 2
            1.0 if feats["has_shortener"] else 0.0,  # 3
            feats["num_exclamations"],   # 4
            feats["num_upper_words"],    # 5
            feats["num_suspicious_words"],  # 6
            feats["html_ratio"],         # 7
        ], dtype=np.float32)

    # NEW: batch processing for enrichment vectors - more efficient for training
    @staticmethod
    def _enrichment_vectors_batch(subjects: List[str], bodies: List[str]) -> np.ndarray:
        """Process multiple (subject, body) pairs into enrichment vectors at once."""
        if len(subjects) != len(bodies):
            raise ValueError("subjects and bodies must have the same length")
        
        vectors = []
        for subject, body in zip(subjects, bodies):
            subject = str(subject) if pd.notna(subject) else ""
            body = str(body) if pd.notna(body) else ""
            vectors.append(SklearnDetector._enrichment_vector(subject, body))
        
        return np.vstack(vectors).astype(np.float32) if vectors else np.array([], dtype=np.float32)

    def analyse(self, subject: str, body: str) -> Dict[str, float | str]:
        if not self.is_ready():
            raise RuntimeError("Sklearn model is not ready; train the detector first.")

        combined_text = f"{subject} {body}".strip()
        cleaned_text = self._clean_text(combined_text)

        # OLD: TF-IDF فقط
        # features = self.vectorizer.transform([cleaned_text])

        # NEW: دمج TF-IDF + المميزات الرقمية
        X_tfidf = self.vectorizer.transform([cleaned_text])
        num_vec = self._enrichment_vector(subject, body).reshape(1, -1)  # NEW
        X_num = sp.csr_matrix(num_vec)  # NEW
        features = sp.hstack([X_tfidf, X_num], format="csr")  # NEW

        proba_array = self.model.predict_proba(features)[0]
        if len(proba_array) == 2:
            proba = float(proba_array[1])
        else:
            # single-class edge case
            proba = 1.0 if self.model.classes_[0] == 1 else 0.0

        label = "suspicious" if proba >= self.threshold else "safe"
        log.debug("ML analysis probability=%s label=%s", proba, label)

        # OLD output محفوظ كما هو + NEW: enrichment
        return {
            "engine": "ml",
            "probability": float(round(proba, 3)),
            "composite_score": float(round(proba, 3)),
            "model_label": label,
            "enrichment": enrichment_features(subject, body),  # NEW
        }

    def train(self, data_path: Path) -> Dict[str, str]:
        dataset = pd.read_csv(data_path)

        # OLD: نفس الأعمدة القديمة
        dataset["clean_text"] = dataset["Email Text"].apply(self._clean_text)
        dataset["label"] = dataset["Email Type"].map({"Phishing Email": 1, "Safe Email": 0})

        # NEW: موضوع (لو موجود) وإلا فاضي — مش هنكسر لو مش موجود
        if "Subject" in dataset.columns:
            subjects = dataset["Subject"].astype(str).fillna("")
        else:
            subjects = pd.Series([""] * len(dataset))

        X_text = dataset["clean_text"]
        y = dataset["label"]

        self.vectorizer = TfidfVectorizer(max_features=5000)
        X_tfidf = self.vectorizer.fit_transform(X_text)

        # NEW: مميزات رقمية من (subject + body الأصلي) - use optimized batch processing
        num_vecs = self._enrichment_vectors_batch(
            subjects.tolist(), 
            dataset["Email Text"].tolist()
        )
        X_num = sp.csr_matrix(num_vecs)  # NEW

        # NEW: دمج
        X_full = sp.hstack([X_tfidf, X_num], format="csr")

        X_train, X_test, y_train, y_test = train_test_split(
            X_full, y, test_size=0.2, random_state=42, stratify=y  # NEW: stratify y أفضل للتوازن
        )
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)

        # NEW: احتمالات للتقييم والجرافات
        y_proba = self.model.predict_proba(X_test)[:, 1]

        report = classification_report(
            y_test, y_pred, target_names=["Safe Email", "Phishing Email"], digits=4
        )

        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        self.vectorizer_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)

        # OLD: كنا بنرجّع report فقط — دلوقتي نزود عليه القيَم للجرافات
        return {
            "report": report,            # OLD (محفوظ)
            "y_true": list(map(int, y_test)),   # NEW
            "y_pred": list(map(int, y_pred)),   # NEW
            "y_proba": list(map(float, y_proba)) # NEW
        }

    @staticmethod
    def _clean_text(text: str) -> str:
        text = str(text).lower()
        text = re.sub(r"http\S+", " ", text)
        text = re.sub(r"[^a-z\s]", " ", text)  
        text = re.sub(r"\s+", " ", text).strip()
        return text


class PhishingDetector:
    """High-level ML"""

    def __init__(
        self,
        model_path: Path,
        vectorizer_path: Path,
        threshold: float = 0.5,
    ):
        self.sklearn_detector = SklearnDetector(model_path, vectorizer_path, threshold)

    def analyse(self, subject: str, body: str) -> Dict[str, float | str]:
        if self.sklearn_detector.is_ready():
            log.debug("PhishingDetector delegating to SklearnDetector")
            return self.sklearn_detector.analyse(subject, body)

        log.error("ML detector not ready when analyse() called")
        raise RuntimeError("No analysis method is currently available.")

    def train(self, data_path: Path) -> Dict[str, str]:
        return self.sklearn_detector.train(data_path)

    def is_ml_ready(self) -> bool:
        return self.sklearn_detector.is_ready()


@lru_cache
def get_detector(
    model_path: str,
    vectorizer_path: str,
    threshold: float = 0.5,
) -> PhishingDetector:
    """Shared detector instance keyed by artifact locations."""
    return PhishingDetector(Path(model_path), Path(vectorizer_path), threshold)
