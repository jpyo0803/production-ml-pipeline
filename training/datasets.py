import os
import pandas as pd
from datetime import datetime
from feast import FeatureStore
from sklearn.model_selection import train_test_split

FEAST_REPO_PATH = os.environ.get("FEAST_REPO_PATH", "/app/feast_repo")
LABEL_URI = os.environ.get("LABEL_URI", "s3://ml-data/raw/application_train.csv")

AWS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "minioadmin")
AWS_SECRET = os.environ.get("AWS_SECRET_ACCESS_KEY", "minioadmin123")
AWS_ENDPOINT = os.environ.get("AWS_ENDPOINT_URL", "http://minio:9000")

def s3_opts():
    return {
        "key": AWS_KEY,
        "secret": AWS_SECRET,
        "client_kwargs": {"endpoint_url": AWS_ENDPOINT},
    }

def load_dataset():
    labels = pd.read_csv(
        LABEL_URI,
        usecols=["SK_ID_CURR", "TARGET"],
        storage_options=s3_opts(),
    )

    store = FeatureStore(repo_path=FEAST_REPO_PATH)

    entity_df = pd.DataFrame({
        "SK_ID_CURR": labels["SK_ID_CURR"],
        "event_timestamp": [datetime(2018, 1, 1)] * len(labels)
    })

    features = [
        "application_features:AMT_INCOME_TOTAL",
        "application_features:AMT_CREDIT",
        "application_features:AMT_ANNUITY",
        "application_features:DAYS_BIRTH",
        "application_features:DAYS_EMPLOYED",
        "bureau_agg_features:bureau_credit_count",
        "bureau_agg_features:bureau_credit_active_count",
        "bureau_agg_features:bureau_credit_days_enddate_mean",
        "bureau_agg_features:bureau_amt_credit_sum",
        "bureau_agg_features:bureau_amt_credit_sum_overdue",
    ]

    feat_df = store.get_historical_features(
        entity_df=entity_df,
        features=features,
    ).to_df()

    df = feat_df.merge(labels, on="SK_ID_CURR", how="inner").fillna(0.0)

    X = df.drop(columns=["SK_ID_CURR", "event_timestamp", "TARGET"]).values
    y = df["TARGET"].values

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    return X_train, y_train, X_val, y_val
