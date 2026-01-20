from feast import FileSource

application_source = FileSource(
    # 파일의 실제 물리적 경로 (URI)
    path="file:///app/feast_repo/data/processed/application.parquet",
    # 데이터의 시점 정보가 담긴 컬럼명
    timestamp_field="event_timestamp",
)

bureau_source = FileSource(
    # 파일의 실제 물리적 경로 (URI)
    path="file:///app/feast_repo/data/processed/bureau_agg.parquet",
    # 데이터의 시점 정보가 담긴 컬럼명
    timestamp_field="event_timestamp",
)