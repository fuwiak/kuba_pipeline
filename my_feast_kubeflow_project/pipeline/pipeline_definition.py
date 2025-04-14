# pipeline/pipeline_definition.py

import kfp
from kfp import dsl
from kfp.dsl import Dataset, Model, Output, Input, Condition
from kfp import compiler

@dsl.component(base_image="python:3.9", 
               packages_to_install=["feast==0.30.0", "pandas", "pyarrow"])  # For ingestion
def ingest_data_component():
    """
    1) Convert CSV to Parquet
    2) feast apply
    3) feast materialize
    """
    import os
    import subprocess
    import pandas as pd

    # Example: read CSV, convert to parquet
    df = pd.read_csv("/app/sp500_raw.csv")
    os.makedirs("/app/data/offline_store", exist_ok=True)
    df.to_parquet("/app/data/offline_store/sp500.parquet")

    # Now do 'feast apply' & 'feast materialize'
    # In a real scenario, you'd have to have your feature_store.yaml in /app/feast_feature_repo 
    # or copy your entire repo. For brevity, let's assume your feast repo is inside /app/feast_feature_repo
    os.chdir("/app/feast_feature_repo")
    subprocess.run(["feast", "apply"], check=True)

    # Materialize full range (example)
    # For a real pipeline, you'd pass start/end times as parameters
    subprocess.run(["feast", "materialize", "--start=2020-01-01", "--end=2023-01-01"], check=True)

@dsl.component(base_image="python:3.9",
               packages_to_install=[
                   "feast==0.30.0", 
                   "tensorflow==2.11.0", 
                   "pandas",
                   "pyarrow", 
                   "scikit-learn"
               ])
def train_model_component(
    # We output the model as a named artifact:
    model_output: Output[Model],
    rmse_output: Output[Dataset]
):
    """
    1) Read historical features from Feast offline store
    2) Train a small LSTM
    3) Calculate metrics (RMSE), store in rmse_output
    4) Save model to model_output.path
    """
    import feast
    import pandas as pd
    import numpy as np
    import tensorflow as tf
    from sklearn.metrics import mean_squared_error

    fs = feast.FeatureStore(repo_path="/app/feast_feature_repo")

    # Suppose we want to train on ticker = "GOOG" only for a simple demonstration:
    entity_df = pd.DataFrame({"ticker": ["GOOG"], "event_timestamp": pd.date_range("2022-01-01", periods=200)})
    
    # Use offline store retrieval
    training_df = fs.get_historical_features(
        entity_df=entity_df,
        features=["sp500_view:close", "sp500_view:volume"]
    ).to_df()

    # Basic data prep
    training_df = training_df.dropna()
    training_df = training_df.sort_values("event_timestamp")
    close_prices = training_df["close"].values

    # For demonstration, let's do a naive LSTM dataset creation
    # E.g. predict the next close price from the previous 5
    window_size = 5
    X, y = [], []
    for i in range(len(close_prices) - window_size):
        X.append(close_prices[i : i+window_size])
        y.append(close_prices[i+window_size])
    X = np.array(X).reshape(-1, window_size, 1)
    y = np.array(y).reshape(-1, 1)

    # Train-test split
    split_idx = int(0.8 * len(X))
    X_train, y_train = X[:split_idx], y[:split_idx]
    X_val, y_val = X[split_idx:], y[split_idx:]

    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(16, input_shape=(window_size, 1), return_sequences=False),
        tf.keras.layers.Dense(1)
    ])
    model.compile(optimizer="adam", loss="mse")
    history = model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=2)

    # Evaluate
    y_pred = model.predict(X_val)
    rmse = mean_squared_error(y_val, y_pred, squared=False)

    # Save the RMSE to the rmse_output artifact
    with open(rmse_output.path, "w") as f:
        f.write(str(rmse))

    # Save the model
    model.save(model_output.path)

@dsl.component(base_image="python:3.9", packages_to_install=["kubernetes", "pyyaml"])
def evaluate_and_deploy_component(
    model_input: Input[Model],
    rmse_input: Input[Dataset],
    # Optional: pass a param for threshold
    threshold: float = 20.0
) -> str:
    """
    1) Read RMSE.
    2) If RMSE < threshold, deploy with KServe using model_input.path.
    3) Return a message string.
    """
    import os
    import subprocess

    with open(rmse_input.path, "r") as f:
        rmse = float(f.read().strip())

    if rmse < threshold:
        # For demonstration, we can do a KServe deployment with a pre-defined YAML.
        # The YAML references a model location in e.g. MinIO, or a volume, etc.
        # You can also dynamically build the KServe YAML. 
        subprocess.run(["kubectl", "apply", "-f", "/app/kserve/kserve_inference_service.yaml"], check=True)
        return f"Model deployed via KServe! RMSE={rmse}"
    else:
        return f"RMSE={rmse} >= {threshold}, skipping deployment."

@dsl.pipeline(
    name="sp500-lstm-pipeline",
    description="Pipeline for SP500 LSTM model training and deployment"
)
def sp500_lstm_pipeline():
    # Step 1: ingest data
    ingest_step = ingest_data_component()

    # Step 2: train model
    train_step = train_model_component()
    train_step.after(ingest_step)  # ensure data ingestion is done

    # Step 3: evaluate & deploy
    deploy_step = evaluate_and_deploy_component(
        model_input=train_step.outputs["model_output"],
        rmse_input=train_step.outputs["rmse_output"]
    )
    deploy_step.after(train_step)

# Компиляция пайплайна с фиксированным путем
if __name__ == "__main__":
    compiler.Compiler().compile(
        pipeline_func=sp500_lstm_pipeline,
        package_path="sp500_lstm_pipeline.json"
    )
