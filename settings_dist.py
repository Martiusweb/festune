# coding: utf-8
#: Application Client ID provided by Spotify
#: You need to request your own application from
#: https://developer.spotify.com/dashboard/
SPOTIFY_APP_CLIENT_ID = ""

#: Application Client matching ``SPOTIFY_APP_CLIENT_ID``
SPOTIFY_APP_CLIENT_SECRET = ""

#: Application redirection URL, after obtaining users authorization.
SPOTIFY_APP_REDIRECTION_URL = "http://localhost:8080/festune"

#: Directory to store persistent data. It may include sensitive data such as
#: authentication tokens.
#: The path can be absolute or relative to the working directory.
DATA_DIR = "data"

# tuple user_id, playlist_id of the "rotating feston playlist"
ROTATING_PLAYLIST = None
