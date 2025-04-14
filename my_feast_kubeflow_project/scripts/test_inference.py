# scripts/test_inference.py

import requests
import json
import feast
import pandas as pd
import os

def get_features_online(ticker: str):
    fs = feast.FeatureStore(repo_path="/app/feast_feature_repo")
    # We assume data is already materialized to the online store
    feature_vector = fs.get_online_features(
        features=["sp500_view:close", "sp500_view:volume"],
        entity_rows=[{"ticker": ticker}]
    ).to_dict()
    return feature_vector

def predict_close_price(ticker: str):
    # 1) get online features
    features = get_features_online(ticker)
    close_val = features["sp500_view:close"][0]
    volume_val = features["sp500_view:volume"][0]

    # 2) call KServe inference
    # Получаем адрес KServe из переменной окружения или используем значение по умолчанию
    kserve_host = os.environ.get("KSERVE_HOST", "http://sp500-lstm-inference.default.svc.cluster.local")
    url = f"{kserve_host}/v1/models/sp500-lstm-inference:predict"
    
    print(f"Calling inference service at: {url}")

    # LSTM expects a shape [batch_size, time_steps, features]
    # В реальном сценарии вы бы использовали данные за последние 5 дней
    input_data = {
        "instances": [
            {
                "time_series_input": [
                    [close_val, volume_val],
                    [close_val, volume_val],
                    [close_val, volume_val],
                    [close_val, volume_val],
                    [close_val, volume_val]
                ]
            }
        ]
    }

    try:
        resp = requests.post(url, json=input_data, timeout=30)
        resp.raise_for_status()  # Проверяем на ошибки HTTP
        print("Response status:", resp.status_code)
        print("Response:", resp.text)
        return resp.json()
    except requests.exceptions.RequestException as e:
        print(f"Error calling inference service: {e}")
        return None

if __name__ == "__main__":
    ticker = os.environ.get("TICKER", "GOOG")
    print(f"Predicting close price for {ticker}")
    predict_close_price(ticker)
