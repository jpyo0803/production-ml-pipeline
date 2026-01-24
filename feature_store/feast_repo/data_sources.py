from feast.infra.offline_stores.contrib.spark_offline_store.spark_source import SparkSource

application_source = SparkSource(
    name="application_source",
    # 파일의 실제 물리적 경로 (URI)
    path="s3a://ml-data/processed/application.parquet",
    file_format="delta",
    # 데이터의 시점 정보가 담긴 컬럼명
    timestamp_field="event_timestamp",
)

bureau_source = SparkSource(
    name="bureau_source",
    # 파일의 실제 물리적 경로 (URI)
    path="s3a://ml-data/processed/bureau_agg.parquet",
    file_format="delta",
    # 데이터의 시점 정보가 담긴 컬럼명
    timestamp_field="event_timestamp",
)