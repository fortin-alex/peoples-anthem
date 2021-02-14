# Script used to recognize faces and to trigger a specific spotify playlist upon recognizing a specific person

from peoples_anthem import PeoplesAnthem

if __name__ == "__main__":

    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-filepath",
        type=str,
        required=True,
        help="Filepath to the model to use for face recognition",
    )

    args = parser.parse_args()

    peoples_anthem = PeoplesAnthem(model_path=args.model_filepath)
    peoples_anthem.recognize_and_play_spotify()