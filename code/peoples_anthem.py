import getpass
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Tuple

import cv2
import joblib
import numpy as np
import torch
from PIL import Image

from config import PLAYLIST, SECRET
from utils.feature_extractor import FeatureExtractor
from utils.frame_extractor import FrameExtractor
from utils.players import SpotifyPlayer

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


class PeoplesAnthem(object):
    def __init__(self):
        self.counter = 0

    def check_for_faces(self, cap: cv2.VideoCapture) -> Tuple[Image.Image, np.array]:
        """
        Method that returns the frame and the detected faces

        Parameters
        ----------
        cap : cv2.VideoCapture
            Video capture from webcam

        Returns
        -------
        Tuple[Image.Image, np.array]
            Tuple of the image capture and array of the coordinates of the detected face
        """
        _, frame = cap.read()

        im = Image.fromarray(frame)
        im = FrameExtractor.preprocess_im(im=im, rotation=180, height_offset=0, brightness_factor=None)
        gray = cv2.cvtColor(np.array(im), cv2.COLOR_BGR2GRAY)

        # This is a good resource, for setting detectMultiScale parameters: https://stackoverflow.com/a/20805153/4490749
        faces_coordinates = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4)

        return im, faces_coordinates

    def increase_counter(self, faces_coordinates: Tuple[np.array]):
        """
        Method that increase the face counter if at least one face is detected

        Parameters
        ----------
        faces_coordinates : Tuple[np.array]
            Array of the coordinates of the detected face
        """

        if len(faces_coordinates) >= 1:  # At least one face detected in this frame
            self.counter += 1
            (_, _, w, h) = FrameExtractor.get_largest_face(faces=faces_coordinates)
            area = w * h
            logger.info(f"face detected on: {datetime.now()}; area was {area}")

    def extract_faces(self, im: Image.Image) -> torch.Tensor:
        """
        Method that extract faces if enough face were detected consecutively

        Since face detection is quick and face extraction is slow, the idea is that we avoid false positives by getting
        `N_CONSECUTIVE_DETECTION` frames consecutively with at least one face detected. Then, we proceed to extracting
        the face.

        Parameters
        ----------
        im : Image.Image
            Image capture from the webcam

        Returns
        -------
        torch.Tensor
            `torch.Tensor` ready to be passed to `facenet` in order to get a vector embedding representing a face
        """

        if self.counter >= N_CONSECUTIVE_DETECTION:
            logger.info(f"Faces detected {N_CONSECUTIVE_DETECTION} times in a row: {datetime.now()}")
            faces = FrameExtractor.get_face_mtcnn(im=im, brightness_factor=BRIGHTNESS_FACTOR)

        else:
            faces = self.counter

        if isinstance(faces, torch.Tensor):
            # facenet expects an image of shape (batch_size, channel, w, h)
            if len(faces.shape) == 3:
                faces = faces.unsqueeze(0)

        return faces

    def reset_video_capture(self, cap: cv2.VideoCapture) -> cv2.VideoCapture:
        """
        Method that reset the video capture and restart the face counter

        Parameters
        ----------
        cap : cv2.VideoCapture
            Video capture from webcam

        Returns
        -------
        cv2.VideoCapture
            Video capture from webcam
        """
        cap.release()
        cv2.destroyAllWindows()

        self.counter = 0
        cap = cv2.VideoCapture(0)

        return cap

    def no_face_detected(self):
        """Method used when no faces are detected"""
        if self.counter > 0:
            logger.info("No face detected: resetting counter.")

        self.counter = 0
        logger.debug("No face detected")
        time.sleep(0.1)

    def recognize_and_play_spotify(self):
        """
        Face detection with opencv and haar cascade for rapid inference. This runs almost instantly on a rpi4
        If detecting faces in `N_CONSECUTIVE_DETECTION` consecutive frames, performs face recognition

        Face recognition uses MTCNN (face extraction) and facenet_pytorch (face recognition).
        This runs in roughly 1.5s on a rpi4
        """
        self.counter = 0
        cap = cv2.VideoCapture(0)

        while cap.isOpened():
            im, faces_coordinates = self.check_for_faces(cap=cap)
            self.increase_counter(faces_coordinates=faces_coordinates)
            extracted_faces = self.extract_faces(im=im)

            if isinstance(extracted_faces, torch.Tensor):

                face_emb = FeatureExtractor.get_embeddings(arr=extracted_faces, pre_process=True)
                face_id = face_recognition_model.predict(face_emb)[0]
                logger.info(f"Detected: {face_id.title()}.")

                # If detecting noise, do nothing. Else, send face_id to music player.
                if face_id.lower() == "misc":
                    continue
                else:
                    SpotifyPlayer.get_and_play_tracks(
                        secret_dict=SECRET, playlist_uri_dict=PLAYLIST, user=face_id, n_tracks=N_TRACKS
                    )

                cap = self.reset_video_capture(cap=cap)

            elif (extracted_faces is None) | (len(faces_coordinates) == 0):
                self.no_face_detected()

    def detect_and_save_image(self, path: str):
        """
        Face detection with opencv and haar cascade for rapid inference. This runs almost instantly on a rpi4
        If detecting faces in `N_CONSECUTIVE_DETECTION` consecutive frames, extract face from image and save to disk

        Face extraction uses MTCNN.
        This runs in roughly 1.0s on a rpi4

        Parameters
        ----------
        path : str
            Directory where to save the images of detected faces. Those will be used for training the face recognition
            model
        """
        self.counter = 0
        cap = cv2.VideoCapture(0)

        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        while cap.isOpened():
            im, faces_coordinates = self.check_for_faces(cap=cap)
            self.increase_counter(faces_coordinates=faces_coordinates)
            extracted_faces = self.extract_faces(im=im)

            if isinstance(extracted_faces, torch.Tensor):
                now = datetime.now().strftime("%Y%m%d-%Hh%Mm%Ss")

                extracted_faces = extracted_faces.squeeze()
                arr = np.transpose(extracted_faces.cpu().numpy(), (1, 2, 0)).astype("int8")
                im = Image.fromarray(arr, mode="RGB")

                im.save(path.joinpath(f"face-{now}.png"))

                cap = self.reset_video_capture(cap=cap)

            elif (extracted_faces is None) | (len(faces_coordinates) == 0):
                self.no_face_detected()
