'''
    원본 application_data.csv 데이터를 불러와서 SK_ID_CURR 별로 집계된 특징들을 생성한 후 parquet 파일로 저장합니다.

    생성된 parquet 파일은 Feast (feature store)에서 사용됩니다.
'''
import os
import pandas as pd
import s3fs

RAW_S3_PREFIX = os.environ.get("RAW_S3_PREFIX", "s3://ml-data/raw")
PROCESSED_S3_PREFIX = os.environ.get("PROCESSED_S3_PREFIX", "s3://ml-data/processed")

AWS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin123")
AWS_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://minio:9000")

USE_COLUMNS = [
    "SK_ID_CURR",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "DAYS_BIRTH",
    "DAYS_EMPLOYED",
]

def s3_opts():
    return {
        "key": AWS_KEY,
        "secret": AWS_SECRET,
        "client_kwargs": {"endpoint_url": AWS_ENDPOINT},
    }

def load_csv(uri: str) -> pd.DataFrame:
    return pd.read_csv(uri, usecols=USE_COLUMNS, storage_options=s3_opts())

def main():
    train_uri = f"{RAW_S3_PREFIX}/application_train.csv"
    test_uri = f"{RAW_S3_PREFIX}/application_test.csv"

    train_df = load_csv(train_uri)
    test_df = load_csv(test_uri)

    df = pd.concat([train_df, test_df], axis=0, ignore_index=True)

    # Feast timestamp
    df["event_timestamp"] = pd.Timestamp("2018-01-01")

    # MinIO(S3)에 저장
    out_uri = f"{PROCESSED_S3_PREFIX}/application.parquet"
    df.to_parquet(out_uri, index=False, storage_options=s3_opts())
    print(f"[OK] wrote {out_uri}")

    # Feast용 LOCAL MIRROR
    fs = s3fs.S3FileSystem(**s3_opts())

    local_dir = "/app/feast_repo/data/processed"
    os.makedirs(local_dir, exist_ok=True)

    with fs.open(out_uri) as f:
        local_df = pd.read_parquet(f)

    local_path = f"{local_dir}/application.parquet"
    local_df.to_parquet(local_path, index=False)

    print(f"[LOCAL MIRROR] wrote {local_path}")

if __name__ == "__main__":
    main()
