import os
import joblib # type: ignore
import pandas as pd # type: ignore
from sklearn.feature_extraction.text import TfidfVectorizer # type: ignore
from sklearn.linear_model import LogisticRegression # type: ignore

DATA_PATH = "data/grievance_data.csv"
MODEL_DIR = "models"

os.makedirs(MODEL_DIR, exist_ok=True)

df = pd.read_csv(DATA_PATH).dropna()

X = df["complaint_text"].astype(str)
y_department = df["department"].astype(str)
y_urgency = df["urgency"].astype(str)

vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
X_vec = vectorizer.fit_transform(X)

dept_model = LogisticRegression(max_iter=1000)
urg_model = LogisticRegression(max_iter=1000)

dept_model.fit(X_vec, y_department)
urg_model.fit(X_vec, y_urgency)

joblib.dump(vectorizer, os.path.join(MODEL_DIR, "vectorizer.pkl"))
joblib.dump(dept_model, os.path.join(MODEL_DIR, "dept_model.pkl"))
joblib.dump(urg_model, os.path.join(MODEL_DIR, "urg_model.pkl"))

print("Training complete.")