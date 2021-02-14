import pickle
import random
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn.pipeline
import torch

_BYTES_TO_MB = 1024 ** 2


def serialize_model(
    model: sklearn.pipeline, parameters: dict, performance: dict, dataset_path: str, output_path: str
) -> dict:
    """
    Function returning a dictionary to be saved to disk with the model and its corresponding metadata

    Parameters
    ----------
    model : sklearn.pipeline
        Pretrained scikit-learn pipeline to save to disk
    parameters : dict
        Dictionary of parameters used for training `model`.
    performance : dict
        Dictionary of `model` performance on train/test dataset
    dataset_path : str
        Path to dataset used to trained the model
    output_path: str
        Path where to save the model

    Returns
    -------
    dict
        Dictionary with 2 keys: `model` and `metadata`
    """

    d = dict()
    metadata = dict()

    model_size_mb = format(sys.getsizeof(pickle.dumps(model)) / _BYTES_TO_MB, ".4f")
    metadata["model_size_mb"] = model_size_mb
    metadata["parameters"] = parameters
    metadata["performance"] = performance
    metadata["dataset_path"] = dataset_path

    d["model"] = model
    d["metadata"] = metadata

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(d, str(output_path), compress=("gzip", 3))

    return output_path


def compute_distance(X: np.array, y: np.array, k: int = 15):
    """
    Function that prints distance between extracted faces

    Parameters
    ----------
    X : np.array
        Embedding of extracted faces
    y : np.array
        Labels corresponding to X, for example: `np.array(["alice", "bob", "alice"])`.
    k : int, optional
        Print distance between `k` randomly selected images from `X`, by default 15
    """
    T = torch.Tensor(X)

    dists = [[(e1 - e2).norm().item() for e2 in T] for e1 in T]
    df = pd.DataFrame(dists, columns=y, index=y)

    idx_lst = random.sample(range(X.shape[0]), k=15)
    print(df.iloc[idx_lst, idx_lst], "\n")
