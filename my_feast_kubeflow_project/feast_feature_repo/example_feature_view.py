# feast_feature_repo/example_feature_view.py

from datetime import timedelta
from feast import Field, FeatureView, FileSource
from feast.types import Float32, String

# Define the data source
sp500_file = FileSource(
    path="data/offline_store/sp500.parquet",
    event_timestamp_column="date",
)

sp500_view = FeatureView(
    name="sp500_view",
    ttl=timedelta(days=365),
    entities=["ticker"],  # The entity is the stock ticker
    schema=[
        Field(name="close", dtype=Float32),
        Field(name="volume", dtype=Float32),
        # add any columns you need, e.g. 'open', 'high', etc.
    ],
    online=True,
    source=sp500_file,
    tags={},
)
