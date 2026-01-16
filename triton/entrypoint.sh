#!/bin/bash
set -e

echo "===== Downloading model from MLflow ====="
python3 download_model.py

echo "===== Start Triton Inference Server ====="
exec tritonserver \
  --model-repository=/models \
  --http-port=8000 \
  --metrics-port=8002 \
  --log-verbose=0