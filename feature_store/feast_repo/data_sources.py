from feast import FileSource

application_source = FileSource(
    path="/app/data/processed/application.parquet",
    timestamp_field="event_timestamp",
)

bureau_source = FileSource(
    path="/app/data/processed/bureau_agg.parquet",
    timestamp_field="event_timestamp",
)