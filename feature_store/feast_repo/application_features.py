from feast import FeatureView, Field
from feast.types import Float32, Int64
from entities import loan
from data_sources import application_source

application_features = FeatureView(
    name="application_features", # FeatureView 이름
    entities=[loan], # 검색 키로 사용할 Entity
    schema=[
        Field(name="AMT_INCOME_TOTAL", dtype=Float32),
        Field(name="AMT_CREDIT", dtype=Float32),
        Field(name="AMT_ANNUITY", dtype=Float32),
        Field(name="DAYS_BIRTH", dtype=Int64),
        Field(name="DAYS_EMPLOYED", dtype=Int64),
    ],
    source=application_source, # 데이터 소스 위치
)