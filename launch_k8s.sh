#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="production-ml-pipeline"

echo "=============================="
echo " Creating Namespace & Context"
echo "=============================="
kubectl apply -f k8s/namespace.yaml
kubectl config set-context --current --namespace="${NAMESPACE}"

echo "Current Namespace:"
kubectl get ns | grep "${NAMESPACE}"

echo "=============================="
echo " Deploying Infrastructure (DB & Storage)"
echo "=============================="

# Provisioner 설치
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/master/deploy/local-path-storage.yaml
kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'

# 마스터 노드의 Taint를 제거하여 모든 포드 배포를 허용
kubectl taint nodes --all node-role.kubernetes.io/control-plane- || true

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
echo " Uploading Raw Data to MinIO"
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
mc mb local/ml-data/processed || true &&
mc cp /application_train.csv local/ml-data/raw/ &&
mc cp /application_test.csv  local/ml-data/raw/ &&
mc cp /bureau.csv            local/ml-data/raw/ &&
mc ls local/ml-data/raw
"

kubectl delete pod minio-uploader --now

echo "=============================="
echo " Creating Secrets"
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
echo " Deploying MLflow & Feature Store"
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
echo " Running Training"
echo "=============================="
kubectl apply -f k8s/training-job.yaml
kubectl wait --for=condition=complete job/training --timeout=1200s

echo "=============================="
echo " Deploying Triton"
echo "=============================="
kubectl apply -f k8s/triton-deployment.yaml
kubectl apply -f k8s/triton-service.yaml

echo "=============================="
echo " Deploying Inference Service"
echo "=============================="

kubectl apply -f k8s/inference-deployment.yaml
kubectl apply -f k8s/inference-service.yaml
kubectl apply -f k8s/inference-hpa.yaml

echo "Waiting 15 seconds for Inference pods to stabilize..."
sleep 15

echo "=============================="
echo " ALL DONE - Service Access"
echo "=============================="

NODE_IP=$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')
PORT=$(kubectl get svc inference -o jsonpath='{.spec.ports[0].nodePort}')
echo "Inference Service is available at: http://${NODE_IP}:${PORT}"
