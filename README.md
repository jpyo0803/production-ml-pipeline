## How to run
#### 데이터 준비
[Kaggle - Home Credit Default Risk](https://www.kaggle.com/competitions/home-credit-default-risk/overview)에서 **application_{train|test}.csv**와 **bureau.csv** 파일을 다운받아 **./data**에 저장. 대략적으로 350MB 필요.

#### Kubernetes 사용시
##### Prerequisite
- Docker 설치 (Docker version 28.0.4)
- Kubernetes 설치 (Client Version: v1.32.2, Kustomize Version: v5.5.0, Server Version: v1.34.0)
- Minikube 설치 (minikube version: v1.37.0)
##### 실행방법
```sh
$ ./launch_k8s.sh
```

##### 추론 요청 예시
```sh
# 단일 요청 (포트번호 xxxxx는 launch_k8s.sh에 실행 마지막에 표시됨)
curl -X POST http://127.0.0.1:xxxxx/predict \
-H "Content-Type: application/json" \
-d '{
"SK_ID_CURR": 100001,
"AMT_INCOME_TOTAL": 202500.0,
"AMT_CREDIT": 406597.5,
"AMT_ANNUITY": 24700.5,
"DAYS_BIRTH": -9461,
"DAYS_EMPLOYED": -637,
"bureau_credit_count": 2,
"bureau_credit_active_count": 1,
"bureau_credit_days_enddate_mean": 365.0,
"bureau_amt_credit_sum": 600000.0,
"bureau_amt_credit_sum_overdue": 0.0
}'
```
```sh
# 배치 요청 (포트번호 xxxxx는 launch_k8s.sh에 실행 마지막에 표시됨)
curl -X POST http://127.0.0.1:xxxxx/predict/batch \
-H "Content-Type: application/json" \
-d '{
"instances": [
{
"AMT_INCOME_TOTAL": 202500.0,
"AMT_CREDIT": 406597.5,
"AMT_ANNUITY": 24700.5,
"DAYS_BIRTH": -9461,
"DAYS_EMPLOYED": -637,
"bureau_credit_count": 2,
"bureau_credit_active_count": 1,
"bureau_credit_days_enddate_mean": 365.0,
"bureau_amt_credit_sum": 600000.0,
"bureau_amt_credit_sum_overdue": 0.0
},
{
"AMT_INCOME_TOTAL": 135000.0,
"AMT_CREDIT": 250000.0,
"AMT_ANNUITY": 18000.0,
"DAYS_BIRTH": -16000,
"DAYS_EMPLOYED": -4000,
"bureau_credit_count": 1,
"bureau_credit_active_count": 1,
"bureau_credit_days_enddate_mean": -1200.0,
"bureau_amt_credit_sum": 300000.0,
"bureau_amt_credit_sum_overdue": 0.0
}
]
}'
```
#### Docker compose 사용시
##### Prerequisite
- Docker 설치 (Docker version 28.0.4)
- Docker compose 설치 (Docker Compose version v2.34.0-desktop.1)
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
```sh
# 단일 요청 
curl -X POST http://localhost:8000/predict \
-H "Content-Type: application/json" \
-d '{
"SK_ID_CURR": 100001,
"AMT_INCOME_TOTAL": 202500.0,
"AMT_CREDIT": 406597.5,
"AMT_ANNUITY": 24700.5,
"DAYS_BIRTH": -9461,
"DAYS_EMPLOYED": -637,
"bureau_credit_count": 2,
"bureau_credit_active_count": 1,
"bureau_credit_days_enddate_mean": 365.0,
"bureau_amt_credit_sum": 600000.0,
"bureau_amt_credit_sum_overdue": 0.0
}'
```
```sh
# 배치 요청 
curl -X POST http://localhost:8000/predict/batch \
-H "Content-Type: application/json" \
-d '{
"instances": [
{
"AMT_INCOME_TOTAL": 202500.0,
"AMT_CREDIT": 406597.5,
"AMT_ANNUITY": 24700.5,
"DAYS_BIRTH": -9461,
"DAYS_EMPLOYED": -637,
"bureau_credit_count": 2,
"bureau_credit_active_count": 1,
"bureau_credit_days_enddate_mean": 365.0,
"bureau_amt_credit_sum": 600000.0,
"bureau_amt_credit_sum_overdue": 0.0
},
{
"AMT_INCOME_TOTAL": 135000.0,
"AMT_CREDIT": 250000.0,
"AMT_ANNUITY": 18000.0,
"DAYS_BIRTH": -16000,
"DAYS_EMPLOYED": -4000,
"bureau_credit_count": 1,
"bureau_credit_active_count": 1,
"bureau_credit_days_enddate_mean": -1200.0,
"bureau_amt_credit_sum": 300000.0,
"bureau_amt_credit_sum_overdue": 0.0
}
]
}'
```