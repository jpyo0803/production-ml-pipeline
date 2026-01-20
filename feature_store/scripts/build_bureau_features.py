'''
    원본 bureau.csv 데이터를 불러와서 SK_ID_CURR 별로 집계된 특징들을 생성한 후 parquet 파일로 저장합니다.
    
    생성된 parquet 파일은 Feast (feature store)에서 사용됩니다.
'''

import os
import pandas as pd

# S3에서 원본 데이터가 저장된 경로
RAW_S3_PREFIX = os.environ.get("RAW_S3_PREFIX", "s3://ml-data/raw")
# S3에 가공된 데이터를 저장할 경로
PROCESSED_S3_PREFIX = os.environ.get("PROCESSED_S3_PREFIX", "s3://ml-data/processed")

# S3 접속 정보
AWS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin123")
AWS_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://minio:9000")

# S3에 접속할때 필요한 옵션들을 딕셔너리 형태로 묶어서 반환
def s3_opts():
    return {
        "key": AWS_KEY,
        "secret": AWS_SECRET,
        "client_kwargs": {"endpoint_url": AWS_ENDPOINT},
    }

def main():
    # Raw CSV 로드
    bureau_uri = f"{RAW_S3_PREFIX}/bureau.csv"
    bureau = pd.read_csv(bureau_uri, storage_options=s3_opts())
    print(f"[Success] Loaded bureau data from {bureau_uri}")

    # SK_ID_CURR 별로 집계
    agg = bureau.groupby("SK_ID_CURR").agg(
        bureau_credit_count=("SK_ID_BUREAU", "count"), # 별 대출 건수
        bureau_credit_active_count=("CREDIT_ACTIVE", lambda x: (x == "Active").sum()), # 활성 대출 건수
        bureau_credit_days_enddate_mean=("DAYS_CREDIT_ENDDATE", "mean"), # 평균 잔여 만기 일수
        bureau_amt_credit_sum=("AMT_CREDIT_SUM", "sum"), # 총 대출 금액
        bureau_amt_credit_sum_overdue=("AMT_CREDIT_SUM_OVERDUE", "sum"), # 연체된 대출 금액
    ).reset_index() # 다시 인덱스 지정
    print(f"[Success] Aggregated bureau features")

    # 데이터 기준일 설정. 현재는 2018-01-01로 고정
    agg["event_timestamp"] = pd.Timestamp("2018-01-01")

    # 가공된 데이터를 S3에 저장
    out_uri = f"{PROCESSED_S3_PREFIX}/bureau_agg.parquet"
    agg.to_parquet(out_uri, index=False, storage_options=s3_opts())
    print(f"[Success] Saved bureau parquet to {out_uri}")

    # 로컬에도 복사본 저장 (Feast에서 사용하기 위함)
    local_dir = "/app/feast_repo/data/processed"
    os.makedirs(local_dir, exist_ok=True)

    local_path = f"{local_dir}/bureau_agg.parquet"
    agg.to_parquet(local_path, index=False)

    print(f"[Success] Copied bureau parquet to local path {local_path}")

if __name__ == "__main__":
    main()
