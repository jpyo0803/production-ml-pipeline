#!/bin/bash
set -e

echo "===== [1] Export model from MLflow to ONNX ====="
python3 download_onnx_model.py

echo "===== [3] Start Triton Inference Server ====="
tritonserver \
  --model-repository=/models \
  --http-port=8000 \
  --metrics-port=8002 \
  --log-verbose=0 &

echo "===== [4] Start FastAPI ====="
uvicorn app_with_triton:app --host 0.0.0.0 --port 8080