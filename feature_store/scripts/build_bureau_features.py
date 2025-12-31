'''
    원본 bureau.csv 데이터를 불러와서 SK_ID_CURR 별로 집계된 특징들을 생성한 후 parquet 파일로 저장합니다.
    생성된 parquet 파일은 Feast (feature store)에서 사용됩니다.
'''

import os
import pandas as pd
import s3fs

RAW_S3_PREFIX = os.environ.get("RAW_S3_PREFIX", "s3://ml-data/raw")
OUT_S3_PREFIX = os.environ.get("OUT_S3_PREFIX", "s3://ml-data/processed")

AWS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin123")
AWS_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://minio:9000")

def s3_opts():
    return {
        "key": AWS_KEY,
        "secret": AWS_SECRET,
        "client_kwargs": {"endpoint_url": AWS_ENDPOINT},
    }

def main():
    # Raw CSV 로드 (MinIO)
    bureau_uri = f"{RAW_S3_PREFIX}/bureau.csv"
    bureau = pd.read_csv(bureau_uri, storage_options=s3_opts())

    # Feature aggregation 
    agg = bureau.groupby("SK_ID_CURR").agg(
        bureau_credit_count=("SK_ID_BUREAU", "count"),
        bureau_credit_active_count=("CREDIT_ACTIVE", lambda x: (x == "Active").sum()),
        bureau_credit_days_enddate_mean=("DAYS_CREDIT_ENDDATE", "mean"),
        bureau_amt_credit_sum=("AMT_CREDIT_SUM", "sum"),
        bureau_amt_credit_sum_overdue=("AMT_CREDIT_SUM_OVERDUE", "sum"),
    ).reset_index()

    # Feast timestamp
    agg["event_timestamp"] = pd.Timestamp("2018-01-01")

    # MinIO(S3)에 저장
    out_uri = f"{OUT_S3_PREFIX}/bureau_agg.parquet"
    agg.to_parquet(out_uri, index=False, storage_options=s3_opts())
    print(f"[OK] wrote {out_uri}")

    # Feast용 LOCAL MIRROR
    fs = s3fs.S3FileSystem(**s3_opts())

    local_dir = "/app/feast_repo/data/processed"
    os.makedirs(local_dir, exist_ok=True)

    with fs.open(out_uri) as f:
        local_df = pd.read_parquet(f)

    local_path = f"{local_dir}/bureau_agg.parquet"
    local_df.to_parquet(local_path, index=False)

    print(f"[LOCAL MIRROR] wrote {local_path}")

if __name__ == "__main__":
    main()
