"""Evaluation script for measuring mean squared error."""
import json
import logging
import pathlib
import pickle
import tarfile

import numpy as np
import pandas as pd
import xgboost

from math import sqrt
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

if __name__ == "__main__":
    logger.debug("Starting evaluation.")
    model_path = "/opt/ml/processing/model/model.tar.gz"
    with tarfile.open(model_path) as tar:
        tar.extractall(path=".")

    logger.debug("Loading xgboost model.")
    model = pickle.load(open("xgboost-model", "rb"))

    logger.debug("Reading test data.")
    test_path = "/opt/ml/processing/test/test.csv"
    df = pd.read_csv(test_path, header=None)

    logger.debug("Reading test data.")
    y_test = df.iloc[:, 0].to_numpy()
    df.drop(df.columns[0], axis=1, inplace=True)
    X_test = xgboost.DMatrix(df.values)

    logger.info("Performing predictions against test data.")
    predictions = model.predict(X_test)

    # See the regression metrics
    # see: https://docs.aws.amazon.com/sagemaker/latest/dg/model-monitor-model-quality-metrics.html
    logger.debug("Calculating mean squared error.")
    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    rmse = sqrt(mse)
    r2 = r2_score(y_test, predictions)
    std = np.std(y_test - predictions)
    report_dict = {
        "regression_metrics": {
            "mae": {
                "value": mae,
                "standard_deviation": std,
            },
            "mse": {
                "value": mse,
                "standard_deviation": std,
            },
            "rmse": {
                "value": rmse,
                "standard_deviation": std,
            },
            "r2": {
                "value": r2,
                "standard_deviation": std,
            },
        },
    }

    output_dir = "/opt/ml/processing/evaluation"
    pathlib.Path(output_dir).mkdir(parents=True, exist_ok=True)

    logger.info("Writing out evaluation report with mse: %f", mse)
    evaluation_path = f"{output_dir}/evaluation.json"
    with open(evaluation_path, "w") as f:
        f.write(json.dumps(report_dict))
