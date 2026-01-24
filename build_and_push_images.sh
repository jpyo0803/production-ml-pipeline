#!/usr/bin/env bash
set -euo pipefail

# Docker Hub 레지스트리 설정
REGISTRY="docker.io/jpyo0803"

build_and_push() {
  local name=$1
  local dir=$2
  local tag="${REGISTRY}/${name}:latest"
  echo "Building and Pushing image: ${tag}..."
  docker build -t "${tag}" -f "${dir}/Dockerfile" .
  docker push "${tag}"
}

echo "=============================="
echo " Build & Push Docker Images"
echo "=============================="

build_and_push feature-store feature_store
build_and_push mlflow-custom mlflow
build_and_push training training
build_and_push triton triton
build_and_push inference inference
build_and_push log-worker log_worker