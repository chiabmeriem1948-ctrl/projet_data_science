# train_ml.py
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

np.random.seed(42)

# 1) dataset simple : sys + dia
N = 5000
sys = np.random.normal(loc=120, scale=20, size=N)
dia = np.random.normal(loc=80, scale=15, size=N)

# 2) label = anomalie selon seuils cliniques
y = ((sys >= 140) | (sys <= 90) | (dia >= 90) | (dia <= 60)).astype(int)

# 3) X = features
X = np.column_stack([sys, dia])

# 4) split train/test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# 5) modèle simple
model = LogisticRegression(max_iter=1000)
model.fit(X_train, y_train)

# 6) évaluation rapide
pred = model.predict(X_test)
print(classification_report(y_test, pred))

# 7) sauvegarde
joblib.dump(model, "bp_logreg.joblib")
print(" Modèle sauvegardé : bp_logreg.joblib")
