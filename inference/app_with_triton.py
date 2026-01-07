import requests
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

TRITON_URL = "http://localhost:8000/v2/models/home_credit_default/infer"

app = FastAPI(title="Home Credit Default Inference API with Triton")

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

# Input schema
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

def to_tensor(reqs: List[PredictionRequest]) -> np.ndarray:
    return np.array(
        [[r.dict()[f] for f in FEATURE_ORDER] for r in reqs],
        dtype=np.float32
    )

# Triton inference logic (공통)
def triton_infer(inputs: np.ndarray):
    payload = {
        "inputs": [
            {
                "name": "input",
                "shape": inputs.shape,   # (B, F)
                "datatype": "FP32",
                "data": inputs.tolist(),
            }
        ]
    }

    res = requests.post(TRITON_URL, json=payload)
    res.raise_for_status()

    outputs = res.json()["outputs"][0]["data"]

    # sigmoid (binary classification 가정)
    probs = [1 / (1 + np.exp(-x)) for x in outputs]

    return probs


# 단일 예측
@app.post("/predict")
def predict(req: PredictionRequest):
    inputs = to_tensor([req])  # shape: (1, F)

    probs = triton_infer(inputs)

    return {
        "probability": probs[0]
    }


# 배치 예측
@app.post("/predict/batch")
def predict_batch(reqs: List[PredictionRequest]):
    inputs = to_tensor(reqs)  # shape: (B, F)

    probs = triton_infer(inputs)

    return {
        "probabilities": probs
    }
