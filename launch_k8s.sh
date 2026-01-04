#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="production-ml-pipeline"

echo "=============================="
echo " Starting Minikube"
echo "=============================="
minikube start

echo "Enabling metrics-server addon..."
minikube addons enable metrics-server

echo "=============================="
echo " Creating namespace"
echo "=============================="
kubectl apply -f k8s/namespace.yaml
kubectl config set-context --current --namespace="${NAMESPACE}"

kubectl get ns
kubectl config view --minify | grep namespace || true

echo "=============================="
echo " Building & loading Docker images"
echo "=============================="

build_and_load() {
  local name=$1
  local dir=$2

  echo "Building image: ${name}"
  (cd "${dir}" && docker build --no-cache -t "${name}:latest" .)

  echo "Loading image into minikube: ${name}"
  minikube image load "${name}:latest"
}

build_and_load mlflow-custom mlflow
build_and_load training training
build_and_load inference inference
build_and_load feature-store feature_store

echo "Loaded images:"
minikube image list | grep -E "mlflow|training|inference|feature-store" || true

echo "=============================="
echo " Deploying Postgres"
echo "=============================="
kubectl apply -f k8s/postgres-pvc.yaml
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml

echo "=============================="
echo " Deploying MinIO"
echo "=============================="
kubectl apply -f k8s/minio-pvc.yaml
kubectl apply -f k8s/minio-deployment.yaml
kubectl apply -f k8s/minio-service.yaml

echo "=============================="
echo " Initializing MinIO buckets"
echo "=============================="
kubectl apply -f k8s/minio-init-job.yaml
kubectl wait --for=condition=complete job/minio-init --timeout=600s

echo "=============================="
echo "Uploading raw CSVs to MinIO..."
echo "=============================="

kubectl run minio-uploader \
  --image=alpine:3.19 \
  --restart=Never \
  --command -- sleep 3600

kubectl wait --for=condition=Ready pod/minio-uploader --timeout=600s

# CSV 복사 (tar 문제 없음)
kubectl cp ./data/application_train.csv minio-uploader:/application_train.csv
kubectl cp ./data/application_test.csv  minio-uploader:/application_test.csv
kubectl cp ./data/bureau.csv            minio-uploader:/bureau.csv

# mc 설치 + 업로드
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

kubectl delete pod minio-uploader

echo "=============================="
echo "Creating MinIO & Postgres credentials secret..."
echo "=============================="

kubectl delete secret minio-credentials -n production-ml-pipeline --ignore-not-found

kubectl create secret generic minio-credentials \
  --from-literal=AWS_ACCESS_KEY_ID=minioadmin \
  --from-literal=AWS_SECRET_ACCESS_KEY=minioadmin123 \
  --from-literal=AWS_DEFAULT_REGION=us-east-1 \
  --from-literal=AWS_ENDPOINT_URL=http://minio:9000 \
  --from-literal=MLFLOW_S3_ENDPOINT_URL=http://minio:9000 \
  -n production-ml-pipeline

kubectl delete secret postgres-credentials -n production-ml-pipeline --ignore-not-found

kubectl create secret generic postgres-credentials \
  --from-literal=POSTGRES_DB=mlflow \
  --from-literal=POSTGRES_USER=mlflow \
  --from-literal=POSTGRES_PASSWORD=mlflow \
  -n production-ml-pipeline

echo "=============================="
echo " Deploying MLflow"
echo "=============================="
kubectl apply -f k8s/mlflow-deployment.yaml
kubectl apply -f k8s/mlflow-service.yaml

echo "=============================="
echo " Running Feature Store (ETL + Feast apply)"
echo "=============================="


echo "Creating Feast repo ConfigMap..."
kubectl delete configmap feast-repo -n "${NAMESPACE}" --ignore-not-found
kubectl create configmap feast-repo \
  --from-file=feature_store/feast_repo \
  -n "${NAMESPACE}"

kubectl apply -f k8s/feast-registry-pvc.yaml
kubectl apply -f k8s/feature-store-job.yaml
kubectl wait --for=condition=complete job/feature-store --timeout=600s
kubectl logs job/feature-store

echo "=============================="
echo " Running Training Job"
echo "=============================="
kubectl apply -f k8s/training-job.yaml
kubectl wait --for=condition=complete job/training --timeout=1200s
kubectl logs job/training

echo "=============================="
echo " Deploying Inference Service"
echo "=============================="
kubectl apply -f k8s/inference-deployment.yaml
kubectl apply -f k8s/inference-service.yaml
kubectl apply -f k8s/inference-hpa.yaml

# 10초 대기
echo "Waiting 10 seconds for Inference pods to be ready..."
sleep 10

echo "=============================="
echo " Exposing Inference Service"
echo "=============================="
minikube service inference -n "${NAMESPACE}"

echo "=============================="
echo " ALL DONE"
echo "=============================="
