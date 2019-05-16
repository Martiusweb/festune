# coding: utf-8

import dataclasses
import sys
import webbrowser

import spotipy
import spotipy.oauth2

import festune
import festune.data
import settings


#: Name of the file in which the token is stored.
DEFAULT_TOKEN_FILE = "spotify-token"


class Error(Exception):
    pass


@dataclasses.dataclass
class Token:
    client_id: str
    client_secret: str
    redirection_url: str
    _token_file: str = DEFAULT_TOKEN_FILE
    _token: str = None

    def get_token(self, interactive=False):
        """
        Return the token of the user.

        The token is read from memory, or the data directory, or, if
        ``interactive`` is ``True``, the user is prompted.

        The token may be refreshed if needed.

        If the token is updated, it is stored on disk.

        :param interactive: if ``True``, the user may be prompted for its
                            credentials
        """
        if not self._token:
            oauth = self._get_oauth()
            # Refresh is done here
            token_info = oauth.get_cached_token()

            if token_info:
                self._token = token_info["access_token"]

        if not self._token and interactive:
            self.prompt_user_credentials()

        return self._token

    @classmethod
    def from_settings(cls):
        """
        Creates a :class:`Token` object from the default settings.
        """
        return cls(
            settings.SPOTIFY_APP_CLIENT_ID,
            settings.SPOTIFY_APP_CLIENT_SECRET,
            settings.SPOTIFY_APP_REDIRECTION_URL)

    def prompt_user_credentials(self):
        """
        Opens user's browser to ask for spotify permissions and stores the
        token with the required scope.
        """
        oauth = self._get_oauth()

        print("Opening your browser...")
        auth_url = oauth.get_authorize_url()
        try:
            webbrowser.open(auth_url)
        except webbrowser.Error:
            print("Please go to", auth_url)

        response = input("Enter the URL you were redirected to: ")

        code = oauth.parse_response_code(response)
        token_info = oauth.get_access_token(code)

        self._token = token_info["access_token"]

        print("Thank you")

    def _get_oauth(self):
        return spotipy.oauth2.SpotifyOAuth(
            self.client_id, self.client_secret, self.redirection_url,
            scope=" ".join(festune.SPOTIFY_SCOPES),
            cache_path=festune.data.get_filename(self._token_file))


def prompt_user_credentials():
    """
    Get the token in interactive mode for future use.
    """
    try:
        Token.from_settings().get_token(interactive=True)
        print("Login successful")
    except Exception as exc:  # noqa
        print(f"Error: {exc}", file=sys.stderr)


def get_spotify():
    """
    Return a spotify api object with the stored token.
    """
    token = Token.from_settings().get_token()
    if not token:
        raise Error("Can not load user's token")

    return spotipy.Spotify(auth=token)
