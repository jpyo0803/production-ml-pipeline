import requests
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

import os

from prometheus_fastapi_instrumentator import Instrumentator

TRITON_HOST = os.getenv("TRITON_HOST", "localhost")
TRITON_PORT = os.getenv("TRITON_PORT", "8000")
MODEL_NAME = os.getenv("MODEL_NAME", "HomeCreditDefaultModel")

# 실제 추론 요청을 보낼 Triton Inference Server의 전체 URL
TRITON_URL = f"http://{TRITON_HOST}:{TRITON_PORT}/v2/models/{MODEL_NAME}/infer"
print(f"Triton Inference URL: {TRITON_URL}")

# API 서버 인스턴스 생인
app = FastAPI(title="Home Credit Default Inference API with Triton")
print("FastAPI app created.")

# 앱 시작 시 메트릭 측정 및 /metrics 엔드포인트 자동 생성
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
print("Prometheus metrics endpoint set up at /metrics.")


'''
    모델 학습시 사용했던 컬럼의 순서를 리스트로 정의

    JSON 데이터는 순서를 보장하지 않으므로,
    모델 입력 시 올바른 순서로 데이터를 배열에 넣어주기 위함
''' 
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

# 클라이언트가 보낼 데이터의 형식을 정의
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
    # 요청받은 데이터 리스트(reqs)를 Triton이 이해할 수 있는 Numpy 배열로 변환
    return np.array(
        [[r.dict()[f] for f in FEATURE_ORDER] for r in reqs], # FEATURE_ORDER 순서대로 값 추출
        dtype=np.float32
    )

# Triton inference logic (공통)
def triton_infer(inputs: np.ndarray):
    # Triton 서버의 HTTP 프로토콜 규격에 맞춰 JSON 페이로드 생페
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

    # Triton 서버에 추론 요청 전송
    res = requests.post(TRITON_URL, json=payload)
    # HTTP 에러(4xx, 5xx) 발생 시 예외 처리
    res.raise_for_status() 

    # Triton 응답에서 모델의 출력 값(Raw logits) 추출
    outputs = res.json()["outputs"][0]["data"]

    # Logit 값을 확률로 변환 (Sigmoid 함수 적용) 
    probs = [1 / (1 + np.exp(-x)) for x in outputs]

    return probs


# 단일 예측
@app.post("/predict")
def predict(req: PredictionRequest):
    print(f"Single prediction request received")

    inputs = to_tensor([req])  # shape: (1, F)

    probs = triton_infer(inputs)

    return {
        "probability": probs[0]
    }


# 배치 예측
@app.post("/predict/batch")
def predict_batch(reqs: List[PredictionRequest]):
    print(f"Batch prediction request received")

    inputs = to_tensor(reqs)  # shape: (B, F)

    probs = triton_infer(inputs)

    return {
        "probabilities": probs
    }
