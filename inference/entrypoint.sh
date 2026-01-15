#!/bin/bash
set -e

echo "===== Downloading model from MLflow ====="
python3 download_from_mlflow.py

echo "===== Start Triton Inference Server ====="
tritonserver \
  --model-repository=/models \
  --http-port=8000 \
  --metrics-port=8002 \
  --log-verbose=0 &

echo "===== Start FastAPI ====="
uvicorn app:app --host 0.0.0.0 --port 8080