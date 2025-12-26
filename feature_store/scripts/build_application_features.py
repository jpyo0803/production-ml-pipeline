'''
    원본 application_data.csv 데이터를 불러와서 SK_ID_CURR 별로 집계된 특징들을 생성한 후 parquet 파일로 저장합니다.

    생성된 parquet 파일은 Feast (feature store)에서 사용됩니다.
'''

import pandas as pd
from pathlib import Path

RAW_DIR = Path("data/raw")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

USE_COLUMNS = [
    "SK_ID_CURR",
    "AMT_INCOME_TOTAL",
    "AMT_CREDIT",
    "AMT_ANNUITY",
    "DAYS_BIRTH",
    "DAYS_EMPLOYED",
]

def load_and_select(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, usecols=USE_COLUMNS)
    return df

def main():
    train_path = RAW_DIR / "application_train.csv"
    test_path = RAW_DIR / "application_test.csv"

    train_df = load_and_select(train_path)
    test_df = load_and_select(test_path)

    '''
        Feast에서는 Train/Test 데이터를 구분하지 않고 사용합니다.

        따라서 두 데이터를 합쳐서 하나의 특징 집합으로 만듭니다.

        실제 모델 학습 시점에 맞춰서 적절하게 Split 해야 합니다.
    '''
    app_df = pd.concat([train_df, test_df], axis=0, ignore_index=True)


    # Feast 호환을 위해 event_timestamp 컬럼 추가 (임의의 고정된 값 사용)
    app_df["event_timestamp"] = pd.Timestamp("2018-01-01")
    app_df["event_timestamp"] = pd.to_datetime(app_df["event_timestamp"])

    '''
        데이터 타입을 Feast에서 지원하는 타입으로 명시적 변환합니다.
    '''
    app_df = app_df.astype({
        "SK_ID_CURR": "int64",
        "AMT_INCOME_TOTAL": "float32",
        "AMT_CREDIT": "float32",
        "AMT_ANNUITY": "float32",
        "DAYS_BIRTH": "int32",
        "DAYS_EMPLOYED": "int32",
    })

    '''
        실제 production 환경에서는 공용 클라우드 스토리지에 저장됩니다.
    '''
    out_path = OUT_DIR / "application.parquet"
    app_df.to_parquet(out_path, index=False)

    print(f"Application features saved to {out_path}")
    print(f"Rows: {len(app_df):,}")

if __name__ == "__main__":
    main()
