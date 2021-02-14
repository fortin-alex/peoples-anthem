import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import torch
from facenet_pytorch import InceptionResnetV1, fixed_image_standardization
from PIL import Image
from tqdm import tqdm

logger = logging.getLogger(__name__)


class FeatureExtractor:
    @staticmethod
    def get_embeddings(arr: np.array, batch_size: int = 4, pre_process: bool = False) -> np.array:
        """
        Method that returns InceptionRestnetV1 embeddings as trained on VGGFace2

        Parameters
        ----------
        arr : np.array
            Batch of images of faces extracted using facenet_pytorch.MTCNN

        batch_size: int
            Batch size used for transforming images into embeddings, by default 4.

        pre_process: bool
            Whether to pre_process the images or not. Rule of thumb, if you loaded your images from disk and these
            images looked normal, you should opt for pre-processing the imag. By default False.

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
            logger.info("Pre-processing images...")
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
        """
        Method that 1. gets the list of labels (for example, the name of the persons to recognize) and 2. extracts the
        `facenet` embeddings from the image from disk.

        Parameters
        ----------
        path : str
            Directory with sub-directories. Each sub-directories contains `.png` of a single person to recognize.

        Returns
        -------
        Tuple[np.array, np.array]
            The embeddings and their corresponding labels

        Notes
        -----
        A good practice is to add an extra directories with miscellaneous images, so that the model learns to recognize
        "other" as its distinct category.
        """
        path = Path(path)

        labels = list(set([x.name for x in path.iterdir()]))
        # Get a dictionary with 1 key per labels and an array of all images correspondings to that labels as its values
        d = {k: np.array(list(map(np.array, map(Image.open, path.joinpath(k).glob("*.png"))))) for k in labels}

        # Create a single `numpy.array` with all images and get a corresponding array with the labels repeated
        # appropriately.
        X = np.vstack([x for x in d.values()])
        y = [item for item, count in zip(d.keys(), [x.shape[0] for x in d.values()]) for i in range(count)]

        X = cls.get_embeddings(arr=X, **kwargs)

        return X, y