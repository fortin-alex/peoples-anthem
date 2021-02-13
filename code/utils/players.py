import logging
import random
import time
import urllib.request
from typing import Any, Dict, List, Union

import requests
import spotipy
import vlc
from spotipy.oauth2 import SpotifyClientCredentials

from config import PLAYLIST, SECRET

logger = logging.getLogger(__name__)


def _play_and_get_info(track: str, position: float = None) -> Dict[str, Any]:
    """Function that plays a song and return the player and metadata

    Parameters
    ----------
    track : str
        Pointer to the song. This can be a URL or a local path.
    position: float
        Will set the position (within the track) to start playing from. For example, 0.5
        will start playing from the middle of the song. If None, plays the song from the
        start, by default, None.

    Returns
    -------
    Dict[str,Any]
        Dictionary with the player and its metadata
    """
    p = vlc.MediaPlayer(track)
    p.audio_set_volume(100)

    if position is not None:
        p.set_position(position)

    p.play()

    while str(p.get_state()) in ["State.NothingSpecial", "State.Opening", "State.Buffering"]:
        time.sleep(0.3)

    duration = p.get_length() / 1000

    d = dict(player=p, metadata=dict(duration=duration))

    return d


class SpotifyPlayer:
    @staticmethod
    def get_credentials(secret_dict: dict, user: str) -> spotipy.client:
        user_secret = secret_dict.get(user)
        client_id = user_secret.get("client_id")
        client_secret = user_secret.get("client_secret")

        auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
        sp = spotipy.Spotify(auth_manager=auth_manager)

        return sp

    @staticmethod
    def get_tracks(sp: spotipy.client, playlist_uri_dict: dict, user: str, n_tracks: int = 5) -> dict:
        """Returns the information of `n_tracks` out of a particular playlist"""
        uri = playlist_uri_dict.get(user)
        playlist = sp.playlist(uri)

        tracks = playlist.get("tracks").get("items")
        tracks = [x.get("track").get("preview_url") for x in tracks]
        tracks = [x for x in tracks if x is not None]

        n_tracks = min(len(tracks), n_tracks)
        tracks = random.sample(tracks, n_tracks)

        return tracks

    @staticmethod
    def play(tracks: Union[str, List]):

        for track_url in tracks:
            logger.info(f"Playing song from url: {track_url}")

            d = _play_and_get_info(track_url)
            time.sleep(d.get("metadata").get("duration"))

            d.get("player").stop()

    @classmethod
    def get_and_play_tracks(cls, secret_dict: dict, playlist_uri_dict: dict, user: str, n_tracks: int = 5):
        sp = cls.get_credentials(secret_dict=secret_dict, user=user)
        tracks = cls.get_tracks(sp=sp, playlist_uri_dict=playlist_uri_dict, user=user, n_tracks=n_tracks)
        cls.play(tracks=tracks)


class LocalPlayer:
    @staticmethod
    def play(tracks: Union[str, List]):

        for track in tracks:
            logger.info(f"Playing song from: {track}")

            d = _play_and_get_info(track)
            time.sleep(d.get("metadata").get("duration"))

            d.get("player").stop()

    @staticmethod
    def play_n_seconds(tracks: Union[str, List], n: int):
        """
        Method that start playing tracks from a random starting point and plays them
        for `n` seconds
        """

        for track in tracks:
            logger.info(f"Playing song from: {track}")

            position = random.random()

            d = _play_and_get_info(track, position=position)
            time.sleep(n)

            d.get("player").stop()


if __name__ == "__main__":
    SpotifyPlayer.get_and_play_tracks(secret_dict=SECRET, playlist_uri_dict=PLAYLIST, user="alex", n_tracks=2)
