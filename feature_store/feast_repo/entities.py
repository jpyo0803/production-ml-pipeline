from feast import Entity

loan = Entity(
    name="loan",
    join_keys=["SK_ID_CURR"],
)