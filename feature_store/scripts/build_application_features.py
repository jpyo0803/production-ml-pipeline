'''
    원본 application_data.csv 데이터를 불러와서 SK_ID_CURR 별로 집계된 특징들을 생성한 후 parquet 파일로 저장합니다.

    생성된 parquet 파일은 Feast (feature store)에서 사용됩니다.
'''

import os
from pyspark.sql.functions import lit, to_timestamp
from common.spark_utils import get_spark_session

# S3에서 원본 데이터가 저장된 경로
RAW_S3_PREFIX = os.environ.get("RAW_S3_PREFIX", "s3://ml-data/raw")
# S3에 가공된 데이터를 저장할 경로
PROCESSED_S3_PREFIX = os.environ.get("PROCESSED_S3_PREFIX", "s3://ml-data/processed")

def main():
    spark = get_spark_session("BuildApplicationFeatures")

    # Raw CSV 로드 (Spark는 필요한 데이터만 로드해 메모리 사용량 절감)
    train_uri = f"{RAW_S3_PREFIX}/application_train.csv"
    test_uri = f"{RAW_S3_PREFIX}/application_test.csv"

    train_df = spark.read.csv(train_uri, header=True, inferSchema=True)
    test_df = spark.read.csv(test_uri, header=True, inferSchema=True)

    use_columns = [
        "SK_ID_CURR",
        "AMT_INCOME_TOTAL",
        "AMT_CREDIT",
        "AMT_ANNUITY",
        "DAYS_BIRTH",
        "DAYS_EMPLOYED",
    ]

    train_df = train_df.select(*use_columns)
    test_df = test_df.select(*use_columns)
    print(f"[Success] Loaded application data from {train_uri} and {test_uri}")

    # Train/Test 데이터 합치기
    df = train_df.unionByName(test_df, allowMissingColumns=True)

    # 데이터 기준일 설정. 현재는 2018-01-01로 고정
    df = df.withColumn("event_timestamp", to_timestamp(lit("2018-01-01")))
    # 가공된 데이터를 S3에 저장
    out_uri = f"{PROCESSED_S3_PREFIX}/application.parquet"
    df.write.format("delta").mode("overwrite").save(out_uri)
    print(f"[Success] Saved application parquet to {out_uri}")

    spark.stop()

if __name__ == "__main__":
    main()
