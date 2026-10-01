import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from pymongo import MongoClient
from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, accuracy_score

col = MongoClient("mongodb://localhost:27017")["traffic_db"]["collisions"]
fields = {"_id": 0, "hour": 1, "weekday": 1, "month": 1, "is_weekend": 1,
          "borough": 1, "factor": 1, "has_injury": 1, "location": 1}
df = pd.DataFrame(list(col.find({}, fields)))

df["lon"] = df["location"].apply(lambda x: x["coordinates"][0])
df["lat"] = df["location"].apply(lambda x: x["coordinates"][1])
df["is_weekend"] = df["is_weekend"].astype(int)

top_factors = df["factor"].value_counts().head(10).index.tolist()
df["factor_group"] = df["factor"].where(df["factor"].isin(top_factors), "Other")

num_cols = ["hour", "weekday", "month", "is_weekend", "lat", "lon"]
cat_cols = ["borough", "factor_group"]
X = df[num_cols + cat_cols]
y = df["has_injury"].astype(int)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y)

pipe = Pipeline([
    ("prep", ColumnTransformer(
        [("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)],
        remainder="passthrough")),
    ("rf", RandomForestClassifier(n_estimators=100, max_depth=12,
                                  min_samples_leaf=20, class_weight="balanced",
                                  n_jobs=1, random_state=42)),
])
pipe.fit(X_train, y_train)

pred = pipe.predict(X_test)
proba = pipe.predict_proba(X_test)[:, 1]
baseline = max(y_test.mean(), 1 - y_test.mean())

print("Baseline (always predict majority):", round(baseline, 3))
print("Model accuracy:", round(accuracy_score(y_test, pred), 3))
print("ROC AUC:", round(roc_auc_score(y_test, proba), 3))
print(classification_report(y_test, pred, target_names=["No injury", "Injury"]))

names = pipe.named_steps["prep"].get_feature_names_out()
imp = pd.Series(pipe.named_steps["rf"].feature_importances_, index=names)
print("Top features:\n", imp.sort_values(ascending=False).head(8))
print("Probability percentiles (33/66):", np.percentile(proba, [33, 66]).round(3))
Path("models").mkdir(exist_ok=True)
joblib.dump({"pipeline": pipe, "top_factors": top_factors}, "models/injury_model.joblib")
print("Saved models/injury_model.joblib")