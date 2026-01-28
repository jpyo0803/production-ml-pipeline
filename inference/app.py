import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime
import json
import os

import aio_pika

import tritonclient.grpc.aio as grpcclient
from tritonclient.utils import InferenceServerException

from prometheus_fastapi_instrumentator import Instrumentator

TRITON_PORT = os.getenv("TRITON_PORT", "8001")
MODEL_NAME = os.getenv("MODEL_NAME", "HomeCreditDefaultModel")

# 실제 추론 요청을 보낼 Triton Inference Server의 전체 URL
TRITON_GRPC_URL = f"triton:{TRITON_PORT}"
print(f"Triton Inference URL: {TRITON_GRPC_URL}")

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
    '''
        FastAPI <-> Triton Inference Server 간 비동기 추론 함수 (gRPC)
    '''

    # gRPC 클라이언트 연결 (Context Manager 사용 권장)
    async with grpcclient.InferenceServerClient(url=TRITON_GRPC_URL) as client:

        '''
            입력 데이터 준비
            "input": config.pbtxt에 정의된 input name
            "FP32": 데이터 타입 (numpy 타입과 일치해야 함)
        '''
        triton_input = grpcclient.InferInput("input", inputs.shape, "FP32")
        triton_input.set_data_from_numpy(inputs)

        # 추론 요청
        try:
            result = await client.infer(
                model_name=MODEL_NAME,
                inputs=[triton_input]
            )
        except InferenceServerException as e:
            print(f"Inference failed: {e}")
            raise

        # 결과 데이터 추출
        output_data = result.as_numpy("output").flatten()

        # 모델 이름 & 버전 가져오기
        response_proto = result.get_response()

        used_model_name = response_proto.model_name
        used_model_version = response_proto.model_version

        # Logit -> Probability 변환 (Sigmoid)
        sigmoid_output = 1 / (1 + np.exp(-output_data))
        probs = sigmoid_output.tolist()

        return probs, used_model_version

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
    print("Single prediction request received")

    inputs = to_tensor([req])  # shape: (1, F)

    probs, used_model_version = await triton_infer_async(inputs)
    print(f"Single inference completed by model version: {used_model_version}")

    await log_to_rabbitmq([req.dict()], probs)
    print("Single log sent to RabbitMQ.")

    return {
        "probability": probs[0]
    }


# 배치 예측
@app.post("/predict/batch")
async def predict_batch(reqs: List[PredictionRequest]):
    print("Batch prediction request received")

    inputs = to_tensor(reqs)  # shape: (B, F)

    probs, used_model_version = await triton_infer_async(inputs)
    print(f"Batch inference completed by model version: {used_model_version}")

    req_dicts = [r.dict() for r in reqs]
    await log_to_rabbitmq(req_dicts, probs)
    print("Batch logs sent to RabbitMQ.")

    return {
        "probabilities": probs
    }
