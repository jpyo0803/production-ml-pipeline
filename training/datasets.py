import os
import pandas as pd
from datetime import datetime
from feast import FeatureStore
from sklearn.model_selection import train_test_split

# Feast Repo 경로
FEAST_REPO_PATH = os.environ.get("FEAST_REPO_PATH", "/app/feast_repo")

# 학습에 사용될 Ground Truth 레이블 경로
LABEL_URI = os.environ.get("LABEL_URI", "s3://ml-data/raw/application_train.csv")

# S3 접근 정보 (Label 가져오기 용도)
AWS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin123")
AWS_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://minio:9000")

# S3 접근 옵션 반환
def s3_opts():
    return {
        "key": AWS_KEY,
        "secret": AWS_SECRET,
        "client_kwargs": {"endpoint_url": AWS_ENDPOINT},
    }

def load_dataset():
    # 레이블 CSV 데이터 로드
    labels = pd.read_csv(
        LABEL_URI,
        usecols=["SK_ID_CURR", "TARGET"],
        storage_options=s3_opts(),
    )

    # Feast 저장소에 연결
    store = FeatureStore(repo_path=FEAST_REPO_PATH)

    # Entity DataFrame 생성
    entity_df = pd.DataFrame({
        "SK_ID_CURR": labels["SK_ID_CURR"], # Label 데이터에 있는 ID 그대로 사용
        "event_timestamp": [datetime(2018, 1, 1)] * len(labels) # 언제 시점의 feature를 가져올지 지정
    })

    # 가져올 feature 목록 정의
    features = [
        "application_features:AMT_INCOME_TOTAL",
        "application_features:AMT_CREDIT",
        "application_features:AMT_ANNUITY",
        "application_features:DAYS_BIRTH",
        "application_features:DAYS_EMPLOYED",
        "bureau_agg_features:bureau_credit_count",
        "bureau_agg_features:bureau_credit_active_count",
        "bureau_agg_features:bureau_credit_days_enddate_mean",
        "bureau_agg_features:bureau_amt_credit_sum",
        "bureau_agg_features:bureau_amt_credit_sum_overdue",
    ]

    # Historical Feature 조회
    feat_df = store.get_historical_features(
        entity_df=entity_df,
        features=features,
    ).to_df() # Pandas DataFrame 형태로 반환

    # feature DataFrame과 레이블을 SK_ID_CURR 기준으로 병합.
    # 결측치는 0.0으로 채움 (현실에서 결측치를 무엇으로 채울지는 도메인 지식에 따라 다름)
    df = feat_df.merge(labels, on="SK_ID_CURR", how="inner").fillna(0.0)

    # 입력 X 준비 (불필요한 컬럼 제거)
    X = df.drop(columns=["SK_ID_CURR", "event_timestamp", "TARGET"]).values
    # 타겟 y 준비
    y = df["TARGET"].values

    # 전체 데이터를 학습용 / 검증용으로 분할
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    return X_train, y_train, X_val, y_val
