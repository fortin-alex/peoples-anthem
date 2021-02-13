# Script used to recognize faces and to trigger a specific spotify playlist upon recognizing a specific person

from peoples_anthem import PeoplesAnthem

if __name__ == "__main__":

    peoples_anthem = PeoplesAnthem()
    peoples_anthem.recognize_and_play_spotify()