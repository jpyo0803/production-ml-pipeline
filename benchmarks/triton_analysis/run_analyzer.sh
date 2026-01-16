#!/bin/bash


# 1. 호스트의 현재 실제 절대 경로를 정확하게 추출
HOST_ABS_PATH=$(readlink -f .)

python $HOST_ABS_PATH/download_model.py

# 2. 실행
docker run --rm -it --net=host \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v "$HOST_ABS_PATH:$HOST_ABS_PATH" \
  -w "$HOST_ABS_PATH" \
  nvcr.io/nvidia/tritonserver:24.01-py3-sdk \
  model-analyzer profile \
  --model-repository "$HOST_ABS_PATH/models" \
  --output-model-repository-path "$HOST_ABS_PATH/results/output_models" \
  --export-path "$HOST_ABS_PATH/results" \
  -f "$HOST_ABS_PATH/config.yaml" \
  --triton-docker-mounts "$HOST_ABS_PATH:$HOST_ABS_PATH:rw" \
  --override-output-model-repository