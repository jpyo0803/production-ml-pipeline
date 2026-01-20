from feast import FeatureView, Field
from feast.types import Float32, Int64
from entities import loan
from data_sources import bureau_source

bureau_features = FeatureView(
    name="bureau_agg_features", # FeatureView 이름
    entities=[loan], # 검색 키로 사용할 Entity
    schema=[
        Field(name="bureau_credit_count", dtype=Int64),
        Field(name="bureau_credit_active_count", dtype=Int64),
        Field(name="bureau_credit_days_enddate_mean", dtype=Float32),
        Field(name="bureau_amt_credit_sum", dtype=Float32),
        Field(name="bureau_amt_credit_sum_overdue", dtype=Float32),
    ],
    source=bureau_source, # 데이터 소스 위치
)