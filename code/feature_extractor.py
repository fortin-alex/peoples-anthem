from pathlib import Path
from typing import Tuple

import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, fixed_image_standardization
from PIL import Image
from torch.utils.mobile_optimizer import optimize_for_mobile
from tqdm import tqdm


class FeatureExtractor:
    @staticmethod
    def get_embeddings(arr: np.array, batch_size: int = 4, pre_process: bool = False) -> np.array:
        """
        Method that returns InceptionRestnetV1 embeddings as trained on VGGFace2

        Parameters
        ----------
        arr : np.array
            Batch of images of faces extracted using facenet_pytorch.MTCNN

        Returns
        -------
        np.array
            InceptionRestnetV1 embeddings as trained on VGGFace2
        """
        device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        resnet = InceptionResnetV1(pretrained='vggface2').eval().to(device)

        T = torch.Tensor(arr).to(device)

        if T.shape[-1] == 3:
            T = T.permute(0, 3, 1, 2)

        if pre_process:
            print("Pre-processing images...")
            T = fixed_image_standardization(T)

        n_batches = T.shape[0] // batch_size + 1

        with torch.no_grad():
            embeddings = [
                resnet(T[batch_size * idx : batch_size * (idx + 1), :, :, :]).detach().cpu()
                for idx in tqdm(range(n_batches))
            ]

        arr = np.vstack(embeddings)

        return arr

    @classmethod
    def prepare_data(cls, path: str, **kwargs) -> Tuple[np.array, np.array]:
        path = Path(path)

        labels = [x.name for x in path.iterdir()]
        d = {k: np.array(list(map(np.array, map(Image.open, path.joinpath(k).glob("*.png"))))) for k in labels}

        X = np.vstack([x for x in d.values()])
        y = [item for item, count in zip(d.keys(), [x.shape[0] for x in d.values()]) for i in range(count)]

        X = cls.get_embeddings(arr=X, **kwargs)

        return X, y


if __name__ == "__main__":
    import random

    import pandas as pd
    from sklearn import svm
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import Normalizer, StandardScaler

    path = Path("/data/faces/mtcnn-detect-2.5/")

    X_train, y_train = FeatureExtractor.prepare_data(path.joinpath("train"), pre_process=True, batch_size=32)
    X_test, y_test = FeatureExtractor.prepare_data(path.joinpath("test"), pre_process=True, batch_size=32)

    T = torch.Tensor(X_train)
    dists = [[(e1 - e2).norm().item() for e2 in T] for e1 in T]
    df = pd.DataFrame(dists, columns=y_train, index=y_train)

    idx_lst = random.sample(range(X_train.shape[0]), k=15)
    print(df.iloc[idx_lst, idx_lst], "\n")

    params = dict(
        nu=0.30,
        kernel="linear",  # ‘linear’, ‘poly’, ‘rbf’, ‘sigmoid’
        degree=3,  # for kernel=="poly" only
        class_weight="balanced",  # None, "balanced"
        decision_function_shape="ovr",
        max_iter=-1,
        verbose=0,
    )

    scaler = Normalizer(norm="l2")  # StandardScaler()
    clf = svm.NuSVC(**params)
    pipe = make_pipeline(scaler, clf)

    pipe.fit(X=X_train, y=y_train)
    d = dict(train=pipe.score(X=X_train, y=y_train), test=pipe.score(X=X_test, y=y_test))
    print(params)
    print(d)
