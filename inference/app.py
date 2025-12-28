import os
import pandas as pd
import mlflow.pyfunc
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import numpy as np
import joblib

# MLflow 설정
MLFLOW_TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow:5000")
MODEL_URI = "models:/HomeCreditDefaultModel@prod"

mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)

print("[INFO] Loading model from MLflow:", MODEL_URI)
model = mlflow.pyfunc.load_model(MODEL_URI)
print("[INFO] Model loaded successfully")

# 스케일러 로드
run_id = model.metadata.run_id

scaler_path = mlflow.artifacts.download_artifacts(
    run_id=run_id,
    artifact_path="preprocessing/scaler.joblib"
)
scaler = joblib.load(scaler_path)

app = FastAPI(title="Home Credit Default Inference API")


# ===== 요청 스키마 =====
class PredictionRequest(BaseModel):
    # 학습에 사용한 feature와 동일해야 함
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


class BatchPredictionRequest(BaseModel):
    instances: List[PredictionRequest]


# ===== 헬스체크 =====
@app.get("/health")
def health():
    return {"status": "ok"}


# ===== 단일 예측 =====
@app.post("/predict")
def predict(req: PredictionRequest):
    df = pd.DataFrame([req.dict()])

    X = scaler.transform(df.values).astype("float32")

    logits = model.predict(X)

    preds = 1 / (1 + np.exp(-logits))  # 시그모이드 함수 적용

    return {"prediction": float(preds[0])}


# ===== 배치 예측 =====
@app.post("/predict/batch")
def predict_batch(req: BatchPredictionRequest):
    df = pd.DataFrame([x.dict() for x in req.instances])

    X = scaler.transform(df.values).astype("float32")

    logits = model.predict(X)

    preds = 1 / (1 + np.exp(-logits))  # 시그모이드 함수 적용

    if hasattr(preds, "values"):
        preds = preds.values

    return {"predictions": preds.tolist()}
