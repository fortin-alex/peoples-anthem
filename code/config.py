from pathlib import Path

# SPOTIFY CLIENT AND SECRET
# This allows the program to use different spotify credential(s) to query spotify playlists using these credentials.
#
# The key of the dictionary must match the person's name used for training the face
# recognition algorithm. The config below is valid if your model was trained to detect
# "alice" and "bob".

SECRET = dict(
    alice=dict(client_id="alice-spotify-client-id", client_secret="alice-spotify-client-secret"),
    bob=dict(client_id="bob-spotify-client-id", client_secret="bob-spotify-client-secret"),
)

# SPOTIFY PLAYLIST URI
# Upon recognizing the face of these user, the program will play these spotify playlist.
# You can obtain a spotify playlist's URI by right-clicking a playlist and selecting: "Share --> Copy spotify URI"

PLAYLIST = dict(
    alice="spotify:playlist:alice",
    bob="spotify:playlist:bob",
)

# PARAMETERS FOR PLAYING A LOCAL SONG
_music_path = Path("/home/pi/Music")
PEOPLE_SONG = dict(
    alice=_music_path.joinpath("alice.mp3"),
    bob=_music_path.joinpath("bob.mp3"),
)
