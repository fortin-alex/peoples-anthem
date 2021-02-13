from pathlib import Path

import pandas as pd
from sklearn import svm
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer

from utils.feature_extractor import FeatureExtractor
from utils.model import compute_distance, serialize_model

_DATASET_PATH = Path("/data/faces/mtcnn-detect-2.5/")
_SAVE_TO_FILE = Path("/models/peoples-anthem/model.v1.pklz")
_PARAMS = params = dict(
    nu=0.30,
    kernel="linear",  # ‘linear’, ‘poly’, ‘rbf’, ‘sigmoid’
    degree=3,  # for kernel=="poly" only
    class_weight="balanced",  # None, "balanced"
    decision_function_shape="ovr",
    max_iter=-1,
    verbose=0,
)

train_path = _DATASET_PATH.joinpath("train")
test_path = _DATASET_PATH.joinpath("test")

X_train, y_train = FeatureExtractor.prepare_data(train_path, pre_process=True, batch_size=32)
X_test, y_test = FeatureExtractor.prepare_data(test_path, pre_process=True, batch_size=32)

compute_distance(X=X_train, y=y_train, k=15)


scaler = Normalizer(norm="l2")  # StandardScaler()
clf = svm.NuSVC(**_PARAMS)
pipe = make_pipeline(scaler, clf)

pipe.fit(X=X_train, y=y_train)

performance = dict(train=pipe.score(X=X_train, y=y_train), test=pipe.score(X=X_test, y=y_test))
output_path = serialize_model(
    model=pipe, parameters=params, performance=performance, dataset_path=_DATASET_PATH, output_path=_SAVE_TO_FILE
)

print(f"Saved serialized model at {output_path}...")