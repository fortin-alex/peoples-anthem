import logging
from pathlib import Path

import pandas as pd
from sklearn import svm
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer

from utils.feature_extractor import FeatureExtractor
from utils.model import serialize_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_PARAMS = params = dict(
    nu=0.30,
    kernel="linear",  # possible options: ‘linear’, ‘poly’, ‘rbf’, ‘sigmoid’
    degree=3,  # notes: for kernel=="poly" only
    class_weight="balanced",  # possible options: None, "balanced"
    decision_function_shape="ovr",
    max_iter=-1,
    verbose=0,
)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input-path",
        type=str,
        required=True,
        help="Directory where images, classified by person, are stored",
    )

    parser.add_argument(
        "--output-filepath",
        type=str,
        required=True,
        help="Filepath where to save the trained model",
    )

    args = parser.parse_args()

    output_filepath = Path(args.output_filepath)

    data_path = Path(args.input_path)
    train_path = data_path.joinpath("train")
    test_path = data_path.joinpath("test")

    assert train_path.is_dir(), f"{train_path} must be a directory but it does not exist."
    assert test_path.is_dir(), f"{test_path} must be a directory but it does not exist."
    assert output_filepath.suffix.lower() in [
        ".pkl",
        ".pklz",
    ], f"The output file must have a suffix in `.pkl` or `.pklz` but got `{output_filepath.name}`."

    # OBTAINING FACE EMBEDDIGNS AND LABELS
    X_train, y_train = FeatureExtractor.prepare_data(train_path, pre_process=True, batch_size=32)
    X_test, y_test = FeatureExtractor.prepare_data(test_path, pre_process=True, batch_size=32)

    # DEFINING MODEL
    scaler = Normalizer(norm="l2")
    clf = svm.NuSVC(**_PARAMS)
    pipe = make_pipeline(scaler, clf)

    # TRAINING AND SAVING MODEL TO DISK
    pipe.fit(X=X_train, y=y_train)

    performance = dict(accuracy_train=pipe.score(X=X_train, y=y_train), accuracy_test=pipe.score(X=X_test, y=y_test))
    performance = {k: float(format(v, ".4f")) for k, v in performance.items()}

    output_path = serialize_model(
        model=pipe, parameters=params, performance=performance, dataset_path=data_path, output_path=output_filepath
    )

    logger.info(f"Saved serialized model at {output_path}...")
    logger.info(f"Trained model performance was: {performance}.")
