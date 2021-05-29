# Script used for saving images of detected faces to disk.
# These images will all have a unique names
#
# After collected enough images, follow the instructions in the `README.md` on how to
# prepare the dataset for training.

from peoples_anthem import PeoplesAnthem

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--path",
        type=str,
        required=True,
        help="Directory where to save the images of detected faces used for training the face recognition model",
    )
    parser.add_argument(
        "--model-filepath",
        type=str,
        required=True,
        help="Filepath to the model to use for face recognition",
    )

    args = parser.parse_args()

    peoples_anthem = PeoplesAnthem(model_path=args.model_filepath)
    peoples_anthem.detect_and_save_image(path=args.path)
