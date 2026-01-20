from feast import Entity

# Entity 정의. Entity는 데이터를 찾을 때 사용하는 Key입니다.
loan = Entity(
    name="loan",
    join_keys=["SK_ID_CURR"],
)