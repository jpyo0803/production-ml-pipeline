'''
    원본 bureau.csv 데이터를 불러와서 SK_ID_CURR 별로 집계된 특징들을 생성한 후 parquet 파일로 저장합니다.
    
    생성된 parquet 파일은 Feast (feature store)에서 사용됩니다.
'''

import os
from pyspark.sql.functions import lit, to_timestamp, count, sum, when, col, mean
from pyspark.sql import SparkSession

# S3에서 원본 데이터가 저장된 경로
RAW_S3_PREFIX = os.environ.get("RAW_S3_PREFIX", "s3://ml-data/raw")
# S3에 가공된 데이터를 저장할 경로
PROCESSED_S3_PREFIX = os.environ.get("PROCESSED_S3_PREFIX", "s3://ml-data/processed")

def get_spark_session(app_name):
    AWS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
    AWS_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin123")
    AWS_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://minio:9000")

    # Dockerfile에서 다운로드 받은 JAR 파일들의 경로
    jar_paths = "/opt/jars/hadoop-aws-3.3.4.jar:/opt/jars/aws-java-sdk-bundle-1.12.262.jar"

    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.driver.extraClassPath", jar_paths) \
        .config("spark.executor.extraClassPath", jar_paths) \
        .config("spark.hadoop.fs.s3a.endpoint", AWS_ENDPOINT) \
        .config("spark.hadoop.fs.s3a.access.key", AWS_KEY) \
        .config("spark.hadoop.fs.s3a.secret.key", AWS_SECRET) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false") \
        .config("spark.hadoop.fs.s3.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
        .getOrCreate()
    
    return spark

def main():
    spark = get_spark_session("BuildBureauFeatures")

    # Raw CSV 로드 (Spark는 필요한 데이터만 로드해 메모리 사용량 절감)
    bureau_uri = f"{RAW_S3_PREFIX}/bureau.csv"
    bureau_df = spark.read.csv(bureau_uri, header=True, inferSchema=True)
    print(f"[Success] Loaded bureau data from {bureau_uri}")

    # SK_ID_CURR 별로 집계
    agg = bureau_df.groupBy("SK_ID_CURR").agg(
        # 1. 별 대출 건수
        count("SK_ID_BUREAU").alias("bureau_credit_count"),
        # 활성 대출 건수 (Conditional Sum)
        sum(when(col("CREDIT_ACTIVE") == "Active", 1).otherwise(0)).alias("bureau_credit_active_count"),
        # 평균 잔여 만기 일수
        mean("DAYS_CREDIT_ENDDATE").alias("bureau_credit_days_enddate_mean"),
        # 총 대출 금액
        sum("AMT_CREDIT_SUM").alias("bureau_amt_credit_sum"),
        # 연체된 대출 금액
        sum("AMT_CREDIT_SUM_OVERDUE").alias("bureau_amt_credit_sum_overdue")
    )
    print(f"[Success] Aggregated bureau features")

    # 데이터 기준일 설정. 현재는 2018-01-01로 고정
    agg = agg.withColumn("event_timestamp", to_timestamp(lit("2018-01-01")))

    # 가공된 데이터를 S3에 저장
    out_uri = f"{PROCESSED_S3_PREFIX}/bureau_agg.parquet"
    agg.write.mode("overwrite").parquet(out_uri)
    print(f"[Success] Saved bureau parquet to {out_uri}")

    # 로컬에도 복사본 저장 (Feast에서 사용하기 위함)
    local_dir = "/app/feast_repo/data/processed"
    os.makedirs(local_dir, exist_ok=True)

    local_path = f"{local_dir}/bureau_agg.parquet"
    agg.write.mode("overwrite").parquet(local_path)

    print(f"[Success] Copied bureau parquet to local path {local_path}")

    spark.stop()

if __name__ == "__main__":
    main()
