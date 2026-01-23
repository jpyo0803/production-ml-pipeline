import os
import json
import time
import uuid
import pika
import pandas as pd
import boto3
from datetime import datetime
from io import BytesIO

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
QUEUE_NAME = "inference_logs"

AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://minio:9000")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY", "minioadmin")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY", "minioadmin123")
AWS_DEFAULT_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "inference-logs")

BATCH_SIZE = 50
FLUSH_INTERVAL = 10  # seconds

s3_client = boto3.client(
    "s3",
    endpoint_url=AWS_ENDPOINT_URL,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_DEFAULT_REGION,
)

log_buffer = []
last_flush_time = time.time()

def flatten_log(log_entries):
    # 중첩된 JSON 구조를 평탄중
    flat_data = []
    for entry in log_entries:
        # FastAPI에서 리스트 형태로 보낸 것을 순회
        # 입력 데이터와 예측 결과를 하나의 행으로 합침
        row = entry["inputs"].copy()
        row["prediction_prob"] = entry["prediction_prob"]
        row["timestamp"] = entry["timestamp"]
        row["model_name"] = entry["model_name"]
        flat_data.append(row)
    return flat_data

def upload_to_s3(buffer):
    if not buffer:
        return
    
    try:
        flat_buffer = []
        for msg in buffer:
            flat_buffer.extend(flatten_log(msg))

        if not flat_buffer:
            return

        df = pd.DataFrame(flat_buffer)

        now = datetime.now()
        partition_path = f"year={now.year}/month={now.month:02d}/day={now.day:02d}"
        file_name = f"{now.strftime('%H%M%S')}_{str(uuid.uuid4())[:8]}.parquet"
        object_key = f"{partition_path}/{file_name}"

        # Parquet 변환
        out_buffer = BytesIO()
        df.to_parquet(out_buffer, index=False, engine='pyarrow')
        out_buffer.seek(0)

        # S3 업로드
        s3_client.upload_fileobj(out_buffer, S3_BUCKET_NAME, object_key)
        print(f"Uploaded {len(df)} log entries to s3://{S3_BUCKET_NAME}/{object_key}")

    except Exception as e:
        print(f"Error uploading logs to S3: {e}")
        # 추후 에러 처리 로직 추가 가능 (재시도 등)

def callback(ch, method, properties, body):
    global last_flush_time

    try:
        payload = json.loads(body)
        log_buffer.append(payload)

        current_time = time.time()

        if len(log_buffer) >= BATCH_SIZE or (current_time - last_flush_time) >= FLUSH_INTERVAL:
            upload_to_s3(log_buffer)
            log_buffer.clear()
            last_flush_time = current_time

        # 처리 완료 통보 (Ack)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        print(f"Error processing message: {e}")
        # 처리 실패 통보 (Nack)
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    print("Connecting to RabbitMQ...")
    while True:
        try:
            params = pika.URLParameters(RABBITMQ_URL)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=QUEUE_NAME, durable=True)

            channel.basic_qos(prefetch_count=BATCH_SIZE)

            channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(f"Connection error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()