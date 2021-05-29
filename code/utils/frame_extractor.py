from pathlib import Path
from typing import List

import cv2
import mmcv
import numpy as np
import torch
from facenet_pytorch import MTCNN
from PIL import Image, ImageEnhance

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

mtcnn_params = dict(
    image_size=160,
    margin=0,
    min_face_size=30,
    thresholds=[0.6, 0.7, 0.7],
    factor=0.709,
    post_process=False,
    selection_method="probability",
    select_largest=True,
    keep_all=False,
    device=device,
)

mtcnn = MTCNN(**mtcnn_params)


class FrameExtractor(object):
    @staticmethod
    def get_video(fp: str) -> cv2.VideoCapture:
        """
        Method that returns a video read from disk by cv2

        Parameters
        ----------
        fp : str
            Filepath to file

        Returns
        -------
        cv2.VideoCapture
            Video read from disk by cv2
        """
        fp = str(fp)
        cap = cv2.VideoCapture(fp)

        return cap

    @staticmethod
    def _close_video(cap: cv2.VideoCapture):
        """
        Method used to close a video capture

        Parameters
        ----------
        cap : cv2.VideoCapture
            Video capture to close
        """

        cap.release()
        cv2.destroyAllWindows()

    @staticmethod
    def _crop_face(im: Image, x: int, y: int, w: int, h: int, scale: float) -> Image:
        """
        Method that, given the coordinates of a faces, returns an Image of that face.

        Parameters
        ----------
        im : Image
            Image with a face in it
        x : int
            Position of the left-most pixel of the face
        y : int
            Position of the top-most pixel of the face
        w : int
            Width of the face in the Image
        h : int
            Height of the face in the Image
        scale : float
            Scaling factor to crop a larger crop than just the face. For example, 1.05 will get a crop 5% larger than
            just the face

        Returns
        -------
        Image
            Image of a face cropped according to the specs
        """

        width, height = im.size
        scale -= 1
        scale /= 2

        W = int(w * scale)
        H = int(h * scale)

        x = min(width, max(0, x - W))
        X = min(width, max(0, x + w + W))

        y = min(height, max(0, y - H))
        Y = min(height, max(0, y + h + H))

        im = im.crop((x, y, X, Y))

        return im

    @staticmethod
    def preprocess_im(
        im: Image, height_offset: int = 100, rotation: int = 180, brightness_factor: float = None
    ) -> Image:
        """
        Method preprocessing an image

        Parameters
        ----------
        im : Image
            Image to be preprocessed
        height_offset : int, optional
            `height_offset` will be cropped from the top of the image. This transformation is applied before `rotation`.
            By default, pikrellcam prints the date and time in its video. Thus, by default 100
        rotation : int, optional
            Rotate the image by `rotation` degrees. On my rpi, the camera is upside down, thus, by default 180
        brightness_factor : float, optional
            Factor by which to scale the brightness by. 2.5 is a good number for a brighter image. If None, leave the
            brightness unadjusted, by default None.

        Returns
        -------
        Image
            Image preprocessed
        """
        w, h = im.size

        im = im.crop((0, height_offset, w, h))
        im = im.rotate(rotation)

        if brightness_factor is not None:
            enhancer = ImageEnhance.Brightness(im)
            im = enhancer.enhance(brightness_factor)

        return im

    @staticmethod
    def get_largest_face(faces: List[tuple]) -> tuple:
        max_area = 0

        for x, y, w, h in faces:
            area = w * h

            if area > max_area:
                face = (x, y, w, h)
                max_area = area

        return face

    @classmethod
    def read_one_frame(cls, cap: cv2.VideoCapture, frame_no: int = 0):
        cap.set(1, frame_no)
        ret, frame = cap.read()

        im = Image.fromarray(frame)
        im = cls.preprocess_im(im=im, height_offset=100, rotation=180, brightness_factor=None)
        display(im)

        cls._close_video(cap=cap)

    @classmethod
    def get_one_frame(cls, cap: cv2.VideoCapture, frame_no: int) -> Image:
        cap.set(1, frame_no)
        _, frame = cap.read()

        im = Image.fromarray(frame)
        im = cls.preprocess_im(im=im, height_offset=100, rotation=180, brightness_factor=None)

        return im

    @classmethod
    def find_frames_with_faces(cls, cap: cv2.VideoCapture, model_path: str, frame_step: int = 5) -> List[dict]:

        model_path = str(model_path)
        face_cascade = cv2.CascadeClassifier(model_path)

        idx = -1
        frame_with_face_idx = []
        while cap.isOpened():
            idx += 1
            ret, frame = cap.read()

            if ret != True:
                cls._close_video(cap=cap)
                return frame_with_face_idx
            elif idx % frame_step != 0:
                continue
            else:
                im = Image.fromarray(frame)
                im = cls.preprocess_im(im=im, height_offset=100, rotation=180, brightness_factor=None)

                gray = cv2.cvtColor(np.array(im), cv2.COLOR_BGR2GRAY)

                faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                if len(faces) >= 1:
                    face = cls.get_largest_face(faces=faces)
                    tmp_dict = dict(idx=idx, face=face)
                    frame_with_face_idx.append(tmp_dict)

    @classmethod
    def _extract_faces_cascade(
        cls, to: str, src: str, model_path: str, scale: float, frame_step: int = 5, rm_faceless: bool = False
    ):
        Path.mkdir(to, parents=True, exist_ok=True)
        to = Path(to)
        fname = Path(src).stem

        cap = cls.get_video(fp=src)
        frame_with_face_idx = cls.find_frames_with_faces(cap=cap, model_path=model_path, frame_step=frame_step)

        cap = cls.get_video(fp=src)
        for i, frame_info in enumerate(frame_with_face_idx):
            fn = fname + f"_{i}.png"
            fn = to.joinpath(fn)

            idx = frame_info.get("idx")
            (x, y, w, h) = frame_info.get("face")

            im = cls.get_one_frame(cap=cap, frame_no=idx)
            im = cls._crop_face(im=im, x=x, y=y, w=w, h=h, scale=scale)
            im.save(fn)

        cls._close_video(cap=cap)

        if (rm_faceless) and (not frame_with_face_idx):
            Path(src).unlink()

    @classmethod
    def get_face_mtcnn(cls, im: Image, brightness_factor: int = 2.5) -> np.array:
        faces = None

        arr = np.array(im)
        im = Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))
        im = cls.preprocess_im(im=im, height_offset=0, rotation=0, brightness_factor=brightness_factor)

        boxes, boxes_probability = mtcnn.detect(im)

        if (boxes_probability[0] is not None) and (boxes_probability[0] > 0.95):
            boxes = boxes[0][None, :]
            faces = mtcnn.extract(img=im, batch_boxes=boxes, save_path=None)

        return faces

    @classmethod
    def _extract_faces_mtcnn(
        cls, to: str, src: str, frame_step: int = 5, rm_faceless: bool = False, brightness_factor: int = 2.5
    ):

        Path.mkdir(to, parents=True, exist_ok=True)
        to = Path(to)
        fname = Path(src).stem

        cap = mmcv.VideoReader(str(src))

        idx = -1
        frame_with_face_idx = []
        for idx, frame in enumerate(cap):
            idx += 1

            if idx % frame_step != 0:
                continue
            else:
                save_to_file = to.joinpath(fname + f"_{idx}.png")

                im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                im = cls.preprocess_im(im=im, height_offset=100, rotation=180, brightness_factor=brightness_factor)

                boxes, boxes_probability = mtcnn.detect(im)

                if (boxes_probability[0] is not None) and (boxes_probability[0] > 0.95):
                    boxes = boxes[0][None, :]
                    faces = mtcnn.extract(img=im, batch_boxes=boxes, save_path=str(save_to_file))

                    if faces is not None:
                        frame_with_face_idx.append(idx)

        if (rm_faceless) and (not frame_with_face_idx):
            Path(src).unlink()

    @classmethod
    def extract_faces(cls, to: str, src: str, detector: str, frame_step: int = 5, rm_faceless: bool = False, **kwargs):
        assert detector.lower() in ["cascade", "mtcnn"], (
            f"Error: `detector` expected to be in ['cascade', 'mtcnn']" + " but got {detector}."
        )

        src = Path(src)

        if detector.lower() == "cascade":
            cls._extract_faces_cascade(to=to, scr=src, frame_step=frame_step, rm_faceless=rm_faceless, **kwargs)
        elif detector.lower() == "mtcnn":
            cls._extract_faces_mtcnn(to=to, src=src, frame_step=frame_step, rm_faceless=rm_faceless, **kwargs)

    @staticmethod
    def delete_processed_videos(videos_path: str, output_path: str):

        videos_list = Path(videos_path).glob("*.mp4")
        output_list = [str(x) for x in Path(output_path).glob("*.png")]

        processed_videos_list = [x for x in videos_list if str(x.stem) in "\t".join(output_list)]

        n_vid_to_delete = len(processed_videos_list)
        plural = "s" if n_vid_to_delete > 1 else ""
        print(f"Deleting {n_vid_to_delete} file{plural}...")

        _ = [x.unlink() for x in processed_videos_list]


if __name__ == "__main__":
    import getpass

    user = getpass.getuser()

    vid_path = f"/home/{user}/pikrellcam/media/videos"
    img_path = "/data/faces/mixed"

    FrameExtractor.delete_processed_videos(videos_path=vid_path, output_path=img_path)
