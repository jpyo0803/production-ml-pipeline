#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="production-ml-pipeline"

echo "=============================="
echo " 1. Starting Minikube"
echo "=============================="
# 메모리와 CPU를 넉넉하게 할당 (ML 워크로드 최적화)
minikube start --memory=8192 --cpus=4

# 로컬 Docker 대신 Minikube 내부 Docker 데몬 사용
echo "Configuring shell to use minikube Docker daemon..."
eval $(minikube docker-env)

echo "Enabling metrics-server addon..."
minikube addons enable metrics-server

echo "=============================="
echo " 2. Creating Namespace & Context"
echo "=============================="
kubectl apply -f k8s/namespace.yaml
kubectl config set-context --current --namespace="${NAMESPACE}"

echo "Current Namespace:"
kubectl get ns | grep "${NAMESPACE}"

echo "=============================="
echo " 3. Building Docker Images (Inside Minikube)"
echo "=============================="
# 별도의 load 과정 없이 바로 내부 데몬에서 빌드합니다.
build_image() {
  local name=$1
  local dir=$2
  echo "Building image: ${name}..."
  (cd "${dir}" && docker build -t "${name}:latest" .)
}

build_image mlflow-custom mlflow
build_image training training
build_image inference inference
build_image feature-store feature_store

echo "Built images in Minikube:"
docker images | grep -E "mlflow|training|inference|feature-store"

echo "=============================="
echo " 4. Deploying Infrastructure (DB & Storage)"
echo "=============================="
# Postgres 배포
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

# MinIO 배포
kubectl apply -f k8s/minio-pvc.yaml
kubectl apply -f k8s/minio-deployment.yaml
kubectl apply -f k8s/minio-service.yaml

echo "Waiting for MinIO to be ready..."
kubectl wait --for=condition=available deployment/minio --timeout=300s

# MinIO 버킷 초기화 Job
kubectl apply -f k8s/minio-init-job.yaml
kubectl wait --for=condition=complete job/minio-init --timeout=600s

echo "=============================="
echo " 5. Uploading Raw Data to MinIO"
echo "=============================="
# 임시 업로더 포드 생성
kubectl run minio-uploader --image=alpine:3.19 --restart=Never --command -- sleep 3600
kubectl wait --for=condition=Ready pod/minio-uploader --timeout=600s

# 로컬 데이터를 포드로 복사
kubectl cp ./data/application_train.csv minio-uploader:/application_train.csv
kubectl cp ./data/application_test.csv  minio-uploader:/application_test.csv
kubectl cp ./data/bureau.csv            minio-uploader:/bureau.csv

# 포드 내부에서 mc(MinIO Client) 설치 및 데이터 업로드
kubectl exec minio-uploader -- sh -c "
apk add --no-cache curl &&
curl -Lo /usr/local/bin/mc https://dl.min.io/client/mc/release/linux-amd64/mc &&
chmod +x /usr/local/bin/mc &&
mc alias set local http://minio:9000 minioadmin minioadmin123 &&
mc mb local/ml-data || true &&
mc mb local/ml-data/raw || true &&
mc cp /application_train.csv local/ml-data/raw/ &&
mc cp /application_test.csv  local/ml-data/raw/ &&
mc cp /bureau.csv            local/ml-data/raw/ &&
mc ls local/ml-data/raw
"

kubectl delete pod minio-uploader --now

echo "=============================="
echo " 6. Creating Secrets"
echo "=============================="
kubectl delete secret minio-credentials postgres-credentials --ignore-not-found

kubectl create secret generic minio-credentials \
  --from-literal=AWS_ACCESS_KEY_ID=minioadmin \
  --from-literal=AWS_SECRET_ACCESS_KEY=minioadmin123 \
  --from-literal=AWS_DEFAULT_REGION=us-east-1 \
  --from-literal=AWS_ENDPOINT_URL=http://minio:9000 \
  --from-literal=MLFLOW_S3_ENDPOINT_URL=http://minio:9000

kubectl create secret generic postgres-credentials \
  --from-literal=POSTGRES_DB=mlflow \
  --from-literal=POSTGRES_USER=mlflow \
  --from-literal=POSTGRES_PASSWORD=mlflow

echo "=============================="
echo " 7. Deploying MLflow & Feature Store"
echo "=============================="
kubectl apply -f k8s/mlflow-deployment.yaml
kubectl apply -f k8s/mlflow-service.yaml

echo "Creating Feast repo ConfigMap..."
kubectl delete configmap feast-repo --ignore-not-found
kubectl create configmap feast-repo --from-file=feature_store/feast_repo

kubectl apply -f k8s/feast-registry-pvc.yaml
kubectl apply -f k8s/feature-store-job.yaml
kubectl wait --for=condition=complete job/feature-store --timeout=600s

echo "=============================="
echo " 8. Running Training & Inference"
echo "=============================="
kubectl apply -f k8s/training-job.yaml
kubectl wait --for=condition=complete job/training --timeout=1200s

kubectl apply -f k8s/inference-deployment.yaml
kubectl apply -f k8s/inference-service.yaml
kubectl apply -f k8s/inference-hpa.yaml

echo "Waiting 15 seconds for Inference pods to stabilize..."
sleep 15

echo "=============================="
echo " ALL DONE - Service Access"
echo "=============================="
minikube service inference -n "${NAMESPACE}"