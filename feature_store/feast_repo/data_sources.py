from feast import FileSource

application_source = FileSource(
    path="file:///app/feast_repo/data/processed/application.parquet",
    timestamp_field="event_timestamp",
)

bureau_source = FileSource(
    path="file:///app/feast_repo/data/processed/bureau_agg.parquet",
    timestamp_field="event_timestamp",
)