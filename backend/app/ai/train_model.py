
import logging
import os
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, accuracy_score, precision_score, recall_score, f1_score, roc_curve, auc
import pandas as pd

from app.ai.phishing_model import get_detector

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

DATA_PATH = Path("data/data.csv")
ARTIFACTS_DIR = Path("artifacts")
MODEL_PATH = ARTIFACTS_DIR / "phishing_model.joblib"
VECTORIZER_PATH = ARTIFACTS_DIR / "tfidf_vectorizer.joblib"
FEEDBACK_PATH = Path("data/feedback.csv")

# Optional controls to avoid retraining on the full 2M+ rows every time
TRAIN_SAMPLE_SIZE = int(os.getenv("TRAIN_SAMPLE_SIZE", "0"))  # 0 means use all
RANDOM_STATE = int(os.getenv("TRAIN_SAMPLE_SEED", "42"))


def _stratified_sample(df: pd.DataFrame, label_col: str, sample_size: int, random_state: int) -> pd.DataFrame:
    """Stratified down-sampling to keep class balance when using a subset."""
    if sample_size <= 0 or len(df) <= sample_size:
        return df

    # compute per-class quota
    value_counts = df[label_col].value_counts()
    total = len(df)
    target_counts = (value_counts / total * sample_size).round().astype(int)

    # ensure no zero after rounding if class exists
    target_counts = target_counts.clip(lower=1)

    parts = []
    for label, count in target_counts.items():
        subset = df[df[label_col] == label]
        take = min(count, len(subset))
        parts.append(subset.sample(n=take, random_state=random_state, replace=False))

    sampled = pd.concat(parts).sample(frac=1.0, random_state=random_state)  # shuffle
    return sampled


def _load_feedback_df() -> Optional[pd.DataFrame]:
    """Load feedback data and map to the training schema if available."""
    if not FEEDBACK_PATH.exists():
        return None

    fb = pd.read_csv(FEEDBACK_PATH)
    if fb.empty:
        return None

    # Map user_label -> Email Type used in training
    label_map = {
        "safe": "Safe Email",
        "suspicious": "Phishing Email",
        "phishing": "Phishing Email",
    }

    fb["Email Type"] = fb["user_label"].map(label_map)
    fb["Email Text"] = fb["body"].astype(str).fillna("")
    fb["Subject"] = fb["subject"].astype(str).fillna("")

    # keep only required columns
    return fb[["Email Text", "Email Type", "Subject"]]

def train():
    log.info("--- Starting the model training process ---")
    
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    log.info(f"Artifacts directory is ready at: {ARTIFACTS_DIR.resolve()}")
    
    detector = get_detector(
        model_path=str(MODEL_PATH),
        vectorizer_path=str(VECTORIZER_PATH)
    )
    
    log.info(f"Loading base data from {DATA_PATH}...")
    try:
        base_df = pd.read_csv(DATA_PATH)

        # Optionally append feedback data
        fb_df = _load_feedback_df()
        if fb_df is not None:
            log.info("Feedback data found; will be merged with base data for training")
            combined_df = pd.concat([base_df, fb_df], ignore_index=True)
        else:
            combined_df = base_df

        # Optional stratified sampling to limit training size
        if TRAIN_SAMPLE_SIZE > 0:
            before = len(combined_df)
            combined_df = _stratified_sample(
                combined_df,
                label_col="Email Type",
                sample_size=TRAIN_SAMPLE_SIZE,
                random_state=RANDOM_STATE,
            )
            log.info("Applied stratified sampling: %s -> %s rows", before, len(combined_df))

        # Persist sampled/merged data temporarily for the detector API
        tmp_path = DATA_PATH.with_name("_training_buffer.csv")
        combined_df.to_csv(tmp_path, index=False)
        log.info("Prepared training buffer at %s", tmp_path)

        report = detector.train(tmp_path)
        log.info("--- Training completed successfully! ---")
        log.info("--- Classification Report ---")
        print(report['report'])

        # Generate visualizations if test data is available
        if "y_true" in report and "y_pred" in report:
            y_true = report["y_true"]
            y_pred = report["y_pred"]

            # Plot class distribution
            plt.figure(figsize=(5,4), dpi=150)
            sns.countplot(x=y_true)
            plt.title("Class Distribution (Test Split)")
            plt.xlabel("Class (0=Safe, 1=Phishing)")
            plt.ylabel("Count")
            plt.tight_layout()
            plt.savefig(ARTIFACTS_DIR / "class_distribution.png")
            plt.close()
            log.info(f"Saved class distribution plot to {ARTIFACTS_DIR / 'class_distribution.png'}")

            # Plot confusion matrix
            cm = confusion_matrix(y_true, y_pred, labels=[0,1])
            plt.figure(figsize=(5,4), dpi=150)
            sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                        xticklabels=["Safe","Phishing"], yticklabels=["Safe","Phishing"])
            plt.title("Confusion Matrix")
            plt.xlabel("Predicted")
            plt.ylabel("Actual")
            plt.tight_layout()
            plt.savefig(ARTIFACTS_DIR / "confusion_matrix.png")
            plt.close()
            log.info(f"Saved confusion matrix plot to {ARTIFACTS_DIR / 'confusion_matrix.png'}")

            # Plot Performance Metrics
            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)
            
            metrics = {
                'Accuracy': accuracy,
                'Precision': precision,
                'Recall': recall,
                'F1-Score': f1
            }
            
            plt.figure(figsize=(8,5), dpi=150)
            bars = plt.bar(metrics.keys(), metrics.values(), color=['#2E86AB', '#A23B72', '#F18F01', '#C73E1D'])
            plt.ylim(0, 1.0)
            plt.ylabel("Score", fontsize=12)
            plt.title("Model Performance Metrics", fontsize=14, fontweight='bold')
            plt.grid(axis='y', alpha=0.3)
            
            # Add value labels on bars
            for bar in bars:
                height = bar.get_height()
                plt.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            
            plt.tight_layout()
            plt.savefig(ARTIFACTS_DIR / "performance_metrics.png", dpi=150, bbox_inches='tight')
            plt.close()
            log.info(f"Saved performance metrics plot to {ARTIFACTS_DIR / 'performance_metrics.png'}")
            log.info(f"Metrics: Accuracy={accuracy:.3f}, Precision={precision:.3f}, Recall={recall:.3f}, F1={f1:.3f}")

    except FileNotFoundError:
        log.error(f"Error: Data file not found at {DATA_PATH.resolve()}")
    except Exception as e:
        log.error(f"An error occurred during training: {e}")

if __name__ == "__main__":
    train()


