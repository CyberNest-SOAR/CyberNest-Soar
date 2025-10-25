import pandas as pd
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report


class PhishingDetector:
    def __init__(self, data_path):
        self.data_path = data_path
        self.vectorizer = TfidfVectorizer(max_features=5000)
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)

    def clean_text(self, text):
        text = str(text).lower()
        text = re.sub(r"http\S+", " ", text)
        text = re.sub(r"[^a-z\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def load_data(self):
        data = pd.read_csv(self.data_path)
        data["clean_text"] = data["Email Text"].apply(self.clean_text)
        data["label"] = data["Email Type"].map({"Phishing Email": 1, "Safe Email": 0})
        return data

    def train(self):
        data = self.load_data()
        X = self.vectorizer.fit_transform(data["clean_text"])
        y = data["label"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)

        print("✅ Model trained successfully!")
        print(classification_report(y_test, y_pred, target_names=["Safe Email", "Phishing Email"]))

    def predict(self, text_list):
        clean_texts = [self.clean_text(text) for text in text_list]
        X = self.vectorizer.transform(clean_texts)
        preds = self.model.predict(X)
        results = ["Phishing Email" if p == 1 else "Safe Email" for p in preds]
        return results
    
#main()
detector = PhishingDetector("Phishing_Email.csv")
detector.train()

emails = ["Meeting at 3pm tomorrow.", "There is a pizza here."]
print(detector.predict(emails))


 

