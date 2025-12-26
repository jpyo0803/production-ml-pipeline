## How to get raw data

[Kaggle - Home Credit Default Risk](https://www.kaggle.com/competitions/home-credit-default-risk/overview)에서 **application_{train|test}.csv**와 **bureau.csv** 파일을 다운받아 **data/raw**에 저장. 대략적으로 350MB 필요.

## How to build docker image
feature_store 디렉토리에서 다음을 실행
```sh
$ docker build -t feature-store .
```

## How to build docker image
feature_store 디렉토리에서 다음을 실행
```sh
$ docker run -it -v $(pwd)/data:/app/data feature-store
```

## How to process raw data
도커 컨테이너 접속 후 feature_store 디렉토리에서 다음을 실행
```sh
$ python scripts/build_bureau_features.py
$ python scripts/build_application_features.py
```
위 과정이 끝나면 data/processed 디렉토리에 다음 파일들이 생성됨

- application.parquet
- bureau_agg.parquet

## How to apply Feast & materialize
(도커 컨테이너 내에서) feast_repo 디렉토리에서 다음을 실행
```sh
$ feast apply
$ feast materialize-incremental $(date +%Y-%m-%d)
```