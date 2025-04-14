# feast_feature_repo/entities.py

from feast import Entity

ticker = Entity(
    name="ticker",
    description="Stock ticker symbol",
)
