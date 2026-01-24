import os
from feast import FeatureStore
from sklearn.model_selection import train_test_split

from pyspark.sql.functions import lit, to_timestamp
from common.spark_utils import get_spark_session

import pandas as pd

# Feast Repo 경로
FEAST_REPO_PATH = os.environ.get("FEAST_REPO_PATH", "/app/feast_repo")

# 학습에 사용될 Ground Truth 레이블 경로
LABEL_URI = os.environ.get("LABEL_URI", "s3://ml-data/raw/application_train.csv")

def load_dataset():
    spark = get_spark_session("LoadDataset")

    # Feast 저장소에 연결
    store = FeatureStore(repo_path=FEAST_REPO_PATH)

    # 레이블 CSV 데이터 로드
    labels_spark_df = spark.read.csv(LABEL_URI, header=True, inferSchema=True).select("SK_ID_CURR", "TARGET")

    # Entity DataFrame 생성
    entity_df = labels_spark_df.select("SK_ID_CURR") \
        .withColumn("event_timestamp", to_timestamp(lit("2018-01-01"))).toPandas()

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
    ).to_df()

    # Label을 Spark에서 Pandas로 변환
    labels_pandas_df = labels_spark_df.toPandas()

    # feature DataFrame과 레이블을 SK_ID_CURR 기준으로 병합.
    # 결측치는 0.0으로 채움 (현실에서 결측치를 무엇으로 채울지는 도메인 지식에 따라 다름)
    df_pandas = pd.merge(feat_df, labels_pandas_df, on="SK_ID_CURR", how="inner").fillna(0.0)
    # Spark 세션 종료
    spark.stop()

    # 입력 X 준비 (불필요한 컬럼 제거)
    X = df_pandas.drop(columns=["TARGET", "event_timestamp", "SK_ID_CURR"], errors='ignore').values
    # 타겟 y 준비
    y = df_pandas["TARGET"].values
    # 전체 데이터를 학습용 / 검증용으로 분할
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    return X_train, y_train, X_val, y_val
