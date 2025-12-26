'''
    원본 bureau.csv 데이터를 불러와서 SK_ID_CURR 별로 집계된 특징들을 생성한 후 parquet 파일로 저장합니다.
    생성된 parquet 파일은 Feast (feature store)에서 사용됩니다.
'''

import pandas as pd

bureau = pd.read_csv("data/raw/bureau.csv")

agg = bureau.groupby("SK_ID_CURR").agg(
    bureau_credit_count=("SK_ID_BUREAU", "count"),
    bureau_credit_active_count=("CREDIT_ACTIVE", lambda x: (x == "Active").sum()),
    bureau_credit_days_enddate_mean=("DAYS_CREDIT_ENDDATE", "mean"),
    bureau_amt_credit_sum=("AMT_CREDIT_SUM", "sum"),
    bureau_amt_credit_sum_overdue=("AMT_CREDIT_SUM_OVERDUE", "sum"),
).reset_index()

agg["event_timestamp"] = pd.Timestamp("2018-01-01")
agg["event_timestamp"] = pd.to_datetime(agg["event_timestamp"])

'''
    실제 production 환경에서는 공용 클라우드 스토리지에 저장됩니다.
'''
agg.to_parquet("data/processed/bureau_agg.parquet")