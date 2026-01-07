import os
import pandas as pd
import mlflow.pyfunc
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import numpy as np

# MLflow 설정
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MODEL_URI = "models:/HomeCreditDefaultModel@prod"

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

print("[INFO] Loading model from MLflow:", MODEL_URI)
model = mlflow.pyfunc.load_model(MODEL_URI)
print("[INFO] Model loaded successfully")

app = FastAPI(title="Home Credit Default Inference API")

FEATURE_ORDER = [
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "DAYS_BIRTH",
    "DAYS_EMPLOYED",
    "bureau_credit_count",
    "bureau_credit_active_count",
    "bureau_credit_days_enddate_mean",
    "bureau_amt_credit_sum",
    "bureau_amt_credit_sum_overdue",
]

# Request schema
class PredictionRequest(BaseModel):
    AMT_INCOME_TOTAL: float
    AMT_CREDIT: float
    AMT_ANNUITY: float
    DAYS_BIRTH: float
    DAYS_EMPLOYED: float
    bureau_credit_count: float
    bureau_credit_active_count: float
    bureau_credit_days_enddate_mean: float
    bureau_amt_credit_sum: float
    bureau_amt_credit_sum_overdue: float

def to_dataframe(reqs: List[PredictionRequest]) -> pd.DataFrame:
    return pd.DataFrame(
        [{f: r.dict()[f] for f in FEATURE_ORDER} for r in reqs],
        columns=FEATURE_ORDER,
    )

# 헬스체크
@app.get("/health")
def health():
    return {"status": "ok"}


# 단일 예측
@app.post("/predict")
def predict(req: PredictionRequest):
    df = to_dataframe([req])   # shape: (1, F)

    logits = model.predict(df)

    probs = 1 / (1 + np.exp(-logits))

    return {
        "probability": float(probs[0])
    }


# 배치 예측
@app.post("/predict/batch")
def predict_batch(reqs: List[PredictionRequest]):
    df = to_dataframe(reqs)  # shape: (B, F)

    logits = model.predict(df)

    probs = 1 / (1 + np.exp(-logits))

    if hasattr(probs, "values"):
        probs = probs.values

    return {
        "probabilities": probs.tolist()
    }
