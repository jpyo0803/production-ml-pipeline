from flask import json
import httpx
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

import os

import aio_pika

from prometheus_fastapi_instrumentator import Instrumentator

TRITON_HOST = os.getenv("TRITON_HOST", "localhost")
TRITON_PORT = os.getenv("TRITON_PORT", "8000")
MODEL_NAME = os.getenv("MODEL_NAME", "HomeCreditDefaultModel")

# 실제 추론 요청을 보낼 Triton Inference Server의 전체 URL
TRITON_URL = f"http://{TRITON_HOST}:{TRITON_PORT}/v2/models/{MODEL_NAME}/infer"
print(f"Triton Inference URL: {TRITON_URL}")

# RabbitMQ 설정
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "inference_logs"
mq_connection = None
mq_channel = None
mq_exchange = None
print(f"RabbitMQ URL: {RABBITMQ_URL}, Queue Name: {QUEUE_NAME}")

# API 서버 인스턴스 생인
app = FastAPI(title="Home Credit Default Inference API with Triton")
print("FastAPI app created.")

# 비동기 HTTP 클라이언트 생성 (재사용)
http_client = httpx.AsyncClient(timeout=10.0)

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

@app.on_event("startup")
async def startup_event():
    # RabbitMQ 연결
    global mq_connection, mq_channel, mq_exchange
    try:
        mq_connection = await aio_pika.connect_robust(RABBITMQ_URL)
        mq_channel = await mq_connection.channel()
        await mq_channel.declare_queue(QUEUE_NAME, durable=True)
        mq_exchange = mq_channel.default_exchange
        print("Connected to RabbitMQ.")
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {e}")

# 앱 종료 시 클라이언트 리소스 정리
@app.on_event("shutdown")
async def shutdown_event():
    await http_client.aclose()
    print("HTTP client closed.")
    if mq_connection:
        await mq_connection.close()
        print("RabbitMQ connection closed.")

def to_tensor(reqs: List[PredictionRequest]) -> np.ndarray:
    # 요청받은 데이터 리스트(reqs)를 Triton이 이해할 수 있는 Numpy 배열로 변환
    return np.array(
        [[r.dict()[f] for f in FEATURE_ORDER] for r in reqs], # FEATURE_ORDER 순서대로 값 추출
        dtype=np.float32
    )

# Triton inference logic (공통)
async def triton_infer_async(inputs: np.ndarray):
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
    res = await http_client.post(TRITON_URL, json=payload)
    # HTTP 에러(4xx, 5xx) 발생 시 예외 처리
    res.raise_for_status() 

    # Triton 응답에서 모델의 출력 값(Raw logits) 추출
    outputs = res.json()["outputs"][0]["data"]

    # Logit 값을 확률로 변환 (Sigmoid 함수 적용) 
    probs = [1 / (1 + np.exp(-x)) for x in outputs]

    return probs

async def log_to_rabbitmq(req_data: List[Dict[str, Any]], probs: List[float]):
    if not mq_exchange:
        print("RabbitMQ exchange not available. Skipping logging.")
        return
    
    # 로그 데이터 구성
    log_entries = []
    timestamp = datetime.utcnow().isoformat()

    for i, req in enumerate(req_data):
        entry = {
            "timestamp": timestamp,
            "inputs": req,
            "prediction_prob": probs[i],
            "model_name": MODEL_NAME
        }
        log_entries.append(entry)

    # 메시지로 직렬화
    message_body = json.dumps(log_entries).encode()

    # 메시지 생성
    message = aio_pika.Message(
        body=message_body,
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
    )

    # 메시지 발행
    await mq_exchange.publish(message, routing_key=QUEUE_NAME)
    print(f"Logged {len(log_entries)} entries to RabbitMQ.")

# 단일 예측
@app.post("/predict")
async def predict(req: PredictionRequest):
    print(f"Single prediction request received")

    inputs = to_tensor([req])  # shape: (1, F)

    probs = await triton_infer_async(inputs)
    print("Single inference completed.")

    await log_to_rabbitmq([req.dict()], probs)
    print("Single log sent to RabbitMQ.")

    return {
        "probability": probs[0]
    }


# 배치 예측
@app.post("/predict/batch")
async def predict_batch(reqs: List[PredictionRequest]):
    print(f"Batch prediction request received")

    inputs = to_tensor(reqs)  # shape: (B, F)

    probs = await triton_infer_async(inputs)
    print("Batch inference completed.")

    req_dicts = [r.dict() for r in reqs]
    await log_to_rabbitmq(req_dicts, probs)
    print("Batch logs sent to RabbitMQ.")

    return {
        "probabilities": probs
    }
