# coding: utf-8
import collections.abc
import dataclasses
import pathlib
import sys
import webbrowser

import spotipy
import spotipy.oauth2

import festune
import festune.data
import festune.exceptions
import settings


#: Name of the file in which the token is stored.
DEFAULT_TOKEN_FILE = "spotify-token"


class Error(festune.exceptions.Error):
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
            try:
                # Refresh is done here
                token_info = oauth.validate_token(
                    oauth.cache_handler.get_cached_token())

                if token_info:
                    self._token = token_info["access_token"]
            except spotipy.oauth2.SpotifyOauthError as exc:
                if exc.error == "invalid_grant" or "invalid_grant" in str(exc):
                    self.discard_token()
                    if interactive:
                        print("Spotify session expired (refresh tokens expire after 6 months). Re-authenticating...")
                    else:
                        raise Error(
                            "Spotify authorization has expired (refresh tokens expire after 6 months). "
                            "Please run 'festune-login' to re-authenticate."
                        ) from exc
                else:
                    raise

        if not self._token and interactive:
            self.prompt_user_credentials()

        return self._token

    def discard_token(self):
        """
        Discard the token from memory and local storage.
        """
        self._token = None
        token_path = festune.data.get_filename(
            self._token_file, create_parent=False)
        if token_path.exists():
            token_path.unlink()

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

        auth_url = oauth.get_authorize_url()
        print("Opening your browser to authorize festune with Spotify...")
        print(f"If your browser does not open automatically, visit this URL:\n{auth_url}\n")
        print("Note: After authorizing, your browser will redirect to your callback URL.")
        print("Even if your browser displays 'Unable to connect' or 'Site can't be reached',")
        print("that is normal! Copy the ENTIRE URL from your browser's address bar and paste it below.\n")

        try:
            webbrowser.open(auth_url)
        except webbrowser.Error:
            pass

        response = input("Enter the URL you were redirected to: ").strip()
        if not response:
            raise Error("No URL or authorization code provided.")

        if response.startswith("code="):
            response = "?" + response

        code = oauth.parse_response_code(response)
        if isinstance(code, str):
            code = code.strip()
            if code.startswith("code="):
                code = code[5:]

        try:
            token_info = oauth.get_access_token(code)
        except spotipy.oauth2.SpotifyOauthError as exc:
            if "invalid_grant" in str(exc) or getattr(exc, "error", None) == "invalid_grant":
                raise Error(
                    "Invalid authorization code.\n"
                    "Common causes:\n"
                    "  - The code was already used. (Authorization codes are strictly single-use).\n"
                    "  - The code expired. (Spotify authorization codes expire within a few minutes).\n"
                    "  - The URL was only partially copied or truncated by the browser address bar.\n"
                    "Please run 'festune-login' again and complete the authorization prompt in a fresh browser session."
                ) from exc
            raise

        self._token = token_info["access_token"]

        print("Thank you")

    def _get_oauth(self):
        cache_handler = spotipy.oauth2.CacheFileHandler(
            cache_path=str(festune.data.get_filename(self._token_file)))
        return spotipy.oauth2.SpotifyOAuth(
            self.client_id, self.client_secret, self.redirection_url,
            scope=" ".join(festune.SPOTIFY_SCOPES),
            cache_handler=cache_handler)


class ResultWrapper(collections.abc.MutableMapping):
    def __init__(self, client, result):
        self.client = client
        self.result = result

    def __len__(self):
        return len(self.result)

    def __iter__(self):
        return iter(self.result)

    def __getitem__(self, key):
        return self.result[key]

    def __contains__(self, key):
        return key in self.result

    def __setitem__(self, key, value):
        self.result[key] = value

    def __delitem__(self, key):
        del self.result[key]

    def __call__(self, method, *args, **kwargs):
        getattr(self.result, method)(*args, **kwargs)

    def __str__(self):
        return str(self.result)

    def __repr__(self):
        return repr(self.result)

    def paginate(self):
        """
        Iterate through the results and load the next page(s).
        """
        result = self.result
        while result:
            yield from result['items']
            result = self.client.next(result)


class Spotify(spotipy.Spotify):
    """
    Add pagination helpers to some requests::

        for playlist in spotify.current_user_playlists().paginate():
            pass

    """
    def _get(self, url, args=None, payload=None, **kwargs):
        result = super()._get(url, args, payload, **kwargs)

        if result and "limit" in kwargs and "offset" in kwargs:
            return ResultWrapper(self, result)

        return result

    def next(self, result):
        result = super().next(result)
        return ResultWrapper(self, result) if result else result


@dataclasses.dataclass
class Object(festune.data.DataObject):
    object_id: str

    @staticmethod
    def get_object_filename(**kwargs):
        """
        :param object_type:
        :param object_id:
        """
        return pathlib.Path(kwargs['object_type'],
                            f"{kwargs['object_id']}.json")


def login():
    """
    Get the token in interactive mode for future use.
    """
    try:
        Token.from_settings().get_token(interactive=True)
        print("Login successful")
    except Exception as exc:  # noqa
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def get_spotify():
    """
    Return a spotify api object with the stored token.
    """
    token = Token.from_settings().get_token()
    if not token:
        raise Error(
            "Can not load user's token. Please run 'festune-login' to authenticate.")

    return Spotify(auth=token)
