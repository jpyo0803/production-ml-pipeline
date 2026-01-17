## How to run
#### 데이터 준비
[Kaggle - Home Credit Default Risk](https://www.kaggle.com/competitions/home-credit-default-risk/overview)에서 **application_{train|test}.csv**와 **bureau.csv** 파일을 다운받아 **./data**에 저장. 대략적으로 350MB 필요.

#### Kubernetes 사용시
##### Prerequisite
- Docker 설치 (Docker Engine Version 28.2.2)
- Kubernetes 설치 (Client Version: v1.35.0, Kustomize Version: v5.7.1, Server Version: v1.30.14)
- Kubeadm 설치 (GitVersion: v1.30.14)
- Helm 설치 (Version: v4.0.5)
- Kubernetes metrics-server 설치 (HPA을 하기위해 필요)
  ```sh
  $ kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
  ```
- Prometheus Stack 설치 (Prometheus, Grafana, Alertmanager 한번에 설치)
  ```sh
  $ helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
  $ helm repo update
  $ helm install obs prometheus-community/kube-prometheus-stack \
  --namespace observability --create-namespace
  ```


##### 실행방법
```sh
$ ./build_and_push_images.sh
$ helm upgrade --install ml-pipeline ./helm \                     
  --namespace production-ml-pipeline \
  --create-namespace \
  --wait \
  --timeout 30m0s
```

##### 추론 요청 예시
단일 요청 (IP는 "$ hostname -I" 명령어를 통해 확인)
```sh
curl -X POST http://x.x.x.x:30080/predict \
  -H "Content-Type: application/json" \
  -d '{
    "AMT_INCOME_TOTAL": 50000,
    "AMT_CREDIT": 200000,
    "AMT_ANNUITY": 15000,
    "DAYS_BIRTH": -12000,
    "DAYS_EMPLOYED": -2000,
    "bureau_credit_count": 3,
    "bureau_credit_active_count": 1,
    "bureau_credit_days_enddate_mean": -500,
    "bureau_amt_credit_sum": 300000,
    "bureau_amt_credit_sum_overdue": 0
  }'
```
배치 요청 (IP는 "$ hostname -I" 명령어를 통해 확인)
```sh
curl -X POST http://x.x.x.x:30080/predict/batch \
  -H "Content-Type: application/json" \
  -d '[
    {
      "AMT_INCOME_TOTAL": 50000,
      "AMT_CREDIT": 200000,
      "AMT_ANNUITY": 15000,
      "DAYS_BIRTH": -12000,
      "DAYS_EMPLOYED": -2000,
      "bureau_credit_count": 3,
      "bureau_credit_active_count": 1,
      "bureau_credit_days_enddate_mean": -500,
      "bureau_amt_credit_sum": 300000,
      "bureau_amt_credit_sum_overdue": 0
    },
    {
      "AMT_INCOME_TOTAL": 80000,
      "AMT_CREDIT": 300000,
      "AMT_ANNUITY": 20000,
      "DAYS_BIRTH": -14000,
      "DAYS_EMPLOYED": -4000,
      "bureau_credit_count": 5,
      "bureau_credit_active_count": 2,
      "bureau_credit_days_enddate_mean": -800,
      "bureau_amt_credit_sum": 500000,
      "bureau_amt_credit_sum_overdue": 1000
    }
  ]'
```
#### Docker compose 사용시
##### Prerequisite
- Docker 설치 (Docker engine Version 28.2.2)
- Docker compose 설치 (Docker Compose version v5.0.1)
- MinIO client 설치 
  ```sh
  $ curl -O https://dl.min.io/client/mc/release/linux-amd64/mc
  $ chmod +x mc
  $ sudo mv mc /usr/local/bin/
  ```

##### 실행방법
```sh
$ docker compose up -d minio minio-init postgres mlflow
$ ./upload_csv.sh
$ docker compose up feature-store # 실행 완료 확인 후 다음 step으로 
$ docker compose up training # 실행 완료 확인 후 다음 step으로
$ docker compose up inference
```

##### 추론 요청 예시
단일 요청 
```sh
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{
    "AMT_INCOME_TOTAL": 50000,
    "AMT_CREDIT": 200000,
    "AMT_ANNUITY": 15000,
    "DAYS_BIRTH": -12000,
    "DAYS_EMPLOYED": -2000,
    "bureau_credit_count": 3,
    "bureau_credit_active_count": 1,
    "bureau_credit_days_enddate_mean": -500,
    "bureau_amt_credit_sum": 300000,
    "bureau_amt_credit_sum_overdue": 0
  }'
```
배치 요청 
```sh
curl -X POST http://localhost:8080/predict/batch \
  -H "Content-Type: application/json" \
  -d '[
    {
      "AMT_INCOME_TOTAL": 50000,
      "AMT_CREDIT": 200000,
      "AMT_ANNUITY": 15000,
      "DAYS_BIRTH": -12000,
      "DAYS_EMPLOYED": -2000,
      "bureau_credit_count": 3,
      "bureau_credit_active_count": 1,
      "bureau_credit_days_enddate_mean": -500,
      "bureau_amt_credit_sum": 300000,
      "bureau_amt_credit_sum_overdue": 0
    },
    {
      "AMT_INCOME_TOTAL": 80000,
      "AMT_CREDIT": 300000,
      "AMT_ANNUITY": 20000,
      "DAYS_BIRTH": -14000,
      "DAYS_EMPLOYED": -4000,
      "bureau_credit_count": 5,
      "bureau_credit_active_count": 2,
      "bureau_credit_days_enddate_mean": -800,
      "bureau_amt_credit_sum": 500000,
      "bureau_amt_credit_sum_overdue": 1000
    }
  ]'

```