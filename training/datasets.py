from config import Config
import pandas as pd
import os

from datetime import datetime
from feast import FeatureStore
from sklearn.model_selection import train_test_split

config = Config()

device = config.device
FEAST_REPO_PATH = os.environ.get("FEAST_REPO_PATH", "/app/feast_repo")

def load_dataset():
    labels = pd.read_csv(config.label_path, usecols=["SK_ID_CURR", "TARGET"])

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

    df = feat_df.merge(labels, on="SK_ID_CURR", how="inner")
    
    df = df.fillna(0.0)
    
    X = df.drop(columns=["SK_ID_CURR", "event_timestamp", "TARGET"]).values
    y = df["TARGET"].values

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    return X_train, y_train, X_val, y_val