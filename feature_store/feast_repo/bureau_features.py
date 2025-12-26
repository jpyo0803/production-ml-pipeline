from feast import FeatureView, Field
from feast.types import Float32, Int64
from entities import loan
from data_sources import bureau_source

bureau_features = FeatureView(
    name="bureau_agg_features",
    entities=[loan],
    schema=[
        Field(name="bureau_credit_count", dtype=Int64),
        Field(name="bureau_credit_active_count", dtype=Int64),
        Field(name="bureau_credit_days_enddate_mean", dtype=Float32),
        Field(name="bureau_amt_credit_sum", dtype=Float32),
        Field(name="bureau_amt_credit_sum_overdue", dtype=Float32),
    ],
    source=bureau_source,
)