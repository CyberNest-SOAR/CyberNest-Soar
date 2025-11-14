

import logging
from pathlib import Path
from app.ai.phishing_model import get_detector

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

DATA_PATH = Path("data/data.csv")
ARTIFACTS_DIR = Path("artifacts")
MODEL_PATH = ARTIFACTS_DIR / "phishing_model.joblib"
VECTORIZER_PATH = ARTIFACTS_DIR / "tfidf_vectorizer.joblib"

def train():
    log.info("--- Starting the model training process ---")
    
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    log.info(f"Artifacts directory is ready at: {ARTIFACTS_DIR.resolve()}")
    
    detector = get_detector(
        model_path=str(MODEL_PATH),
        vectorizer_path=str(VECTORIZER_PATH)
    )
    
    log.info(f"Loading data from {DATA_PATH}...")
    try:
        report = detector.train(DATA_PATH)
        log.info("--- Training completed successfully! ---")
        log.info("--- Classification Report ---")
        print(report['report'])
        log.info(f"Model saved to: {MODEL_PATH.resolve()}")
        log.info(f"Vectorizer saved to: {VECTORIZER_PATH.resolve()}")
        
    except FileNotFoundError:
        log.error(f"Error: Data file not found at {DATA_PATH.resolve()}")
    except Exception as e:
        log.error(f"An error occurred during training: {e}")

if __name__ == "__main__":
    train()

 

