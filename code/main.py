import getpass
import logging
import time
from datetime import datetime
from pathlib import Path

import cv2
import joblib
import numpy as np
from PIL import Image

from config import PLAYLIST, SECRET
from feature_extractor import FeatureExtractor
from frame_extractor import FrameExtractor
from players import SpotifyPlayer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

N_TRACKS = 2  # Play `N_TRACKS` from your playlist
N_CONSECUTIVE_DETECTION = 3  # Number of face to detect before identifying
BRIGHTNESS_FACTOR = 2.5  # Increase the brightness of each picture before sending it to `FrameExtractor.get_face_mtcnn`

# Model for face recognition from facenet embeddings
FACE_RECOGNITION_MODEL_PATH = Path("/models/peoples-anthem/model.v1.pklz")

# Model for face detection
FACE_DETECTION_MODEL_PATH = Path(f"/home/{getpass.getuser()}/models-cache/face-cascade/")
FACE_DETECTION_MODEL_FILEPATH = FACE_DETECTION_MODEL_PATH.joinpath("haarcascade_frontalface_default.xml")

# SETUP FACE DETECTION
face_cascade = cv2.CascadeClassifier(str(FACE_DETECTION_MODEL_FILEPATH))
face_recognition_model = joblib.load(str(FACE_RECOGNITION_MODEL_PATH)).get("model")


def run():
    """
    Face detection with opencv and haar cascade for rapid inference. This runs almost instantly on a rpi4
    If detecting faces in `N_CONSECUTIVE_DETECTION` consecutive frames, performs face recognition

    Face recognition uses MTCNN (face extraction) and facenet_pytorch (face recognition).
    This runs in roughly 1.5s on a rpi4
    """
    counter = 0
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        _, frame = cap.read()

        im = Image.fromarray(frame)
        im = FrameExtractor.preprocess_im(im=im, rotation=180, height_offset=0, brightness_factor=None)
        gray = cv2.cvtColor(np.array(im), cv2.COLOR_BGR2GRAY)

        # This is a good resource, for setting detectMultiScale parameters: https://stackoverflow.com/a/20805153/4490749
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

        if len(faces) >= 1:  # At least one face detected in this frame
            counter += 1
            (_, _, w, h) = FrameExtractor.get_largest_face(faces=faces)
            area = w * h
            logger.info(f"face detected on: {datetime.now()}; area was {area}")
            if counter >= N_CONSECUTIVE_DETECTION:
                logger.info(f"Faces detected {N_CONSECUTIVE_DETECTION} times in a row: {datetime.now()}")

                faces = FrameExtractor.get_face_mtcnn(im=im, brightness_factor=BRIGHTNESS_FACTOR)

                if faces is not None:
                    # facenet expects an image of shape (batch_size, channel, w, h)
                    if len(faces.shape) == 3:
                        faces = faces.unsqueeze(0)

                    face_emb = FeatureExtractor.get_embeddings(arr=faces, pre_process=True)
                    face_id = face_recognition_model.predict(face_emb)[0]
                    logger.info(f"Detected: {face_id.title()}.")

                    # If detecting noise, do nothing. Else, send face_id to music player.
                    if face_id.lower() == "misc":
                        continue
                    else:
                        SpotifyPlayer.get_and_play_tracks(
                            secret_dict=SECRET, playlist_uri_dict=PLAYLIST, user=face_id, n_tracks=N_TRACKS
                        )
                        cap.release()
                        cv2.destroyAllWindows()

                    counter = 0
                    cap = cv2.VideoCapture(0)

        else:  # No face detected in this frame
            if counter > 0:
                logger.info("No face detected: resetting counter.")
            counter = 0
            logger.debug("No face detected")
            time.sleep(0.1)


if __name__ == "__main__":
    run()

    cap.release()
    cv2.destroyAllWindows()
