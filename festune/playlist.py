# coding: utf-8
from typing import List, Optional

import dataclasses
import pathlib
import re

import festune.exceptions
import festune.spotify


#: Match a "Playlist feston"
PLAYLIST_NAME_DATE_REGEX = re.compile(
    r"Playlist Feston (?:de |d'|vom |of )(?P<month_name>\w+) '(?P<year>\d{2})")

# Parse the month number from the month name in the playlist
_MONTH_NUMBERS_BY_NAME = {
    "Janvier": 1,
    "Février": 2,
    "Februar": 2,
    "Mars": 3,
    "Avril": 4,
    "Mai": 5,
    "Juin": 6,
    "Juillet": 7,
    "Aout": 8,
    "Août": 8,
    "Septembre": 9,
    "Octobre": 10,
    "Novembre": 11,
    "Décembre": 12,
    "Decembre": 12,
    "Noël": 12,
}


class Error(festune.exceptions.Error):
    pass


def load_all_from_server(spotify):
    """
    Load all "Feston" playlists.
    """
    for playlist in spotify.current_user_playlists().paginate():
        if is_feston(playlist['name']):
            yield FestonPlaylist.from_api(playlist)


def load_from_server(spotify, user_id, playlist_id):
    """
    Load the given playlist.
    """
    return FestonPlaylist.from_api(spotify.user_playlist(user_id, playlist_id))


def load_tracks_from_server(spotify, playlist):
    tracks = spotify.user_playlist_tracks(playlist.user_id, playlist.object_id)
    for track in tracks.paginate():
        yield PlaylistTrack.from_api(
            playlist.user_id, playlist.object_id, track["track"])


def is_feston(playlist_name):
    """
    Return true if the list should be picked.
    """
    return (playlist_name.startswith("Playlist Feston")
            and 'spéciale' not in playlist_name)


def month_number_from(month_name):
    """
    Return the month number (from 1 to 12) from ``month_name``.

    :param month_name:name of the month
    :raise: ValueError if the month name is unknown
    """
    if month_name not in _MONTH_NUMBERS_BY_NAME:
        raise ValueError(f"Unknown month {month_name}")

    return _MONTH_NUMBERS_BY_NAME[month_name]


@dataclasses.dataclass
class Playlist(festune.spotify.Object):
    """
    A playlist.
    """
    name: str
    user_id: str
    external_url: str
    image: Optional[str]
    public: bool
    snapshot_id: Optional[str]
    nb_tracks: int

    @property
    def uri(self):
        return f"spotify:playlist:{self.object_id}"

    @classmethod
    def from_api(cls, playlist_json):
        if playlist_json.get("type") != "playlist":
            raise ValueError("Supplied json object is not a playlist")

        if "images" in playlist_json and playlist_json["images"]:
            image = playlist_json["images"][0]["url"]
        else:
            image = None

        return cls(playlist_json["type"],
                   playlist_json["id"],
                   playlist_json["name"],
                   playlist_json["owner"]["id"],
                   playlist_json["external_urls"]["spotify"],
                   image,
                   playlist_json.get("public", False),
                   playlist_json["snapshot_id"],
                   playlist_json["tracks"]["total"])

    @staticmethod
    def get_object_filename(**kwargs):
        """
        :param object_type:
        :param user_id:
        :param object_id:
        """
        return pathlib.Path(kwargs['object_type'],
                            f"{kwargs['user_id']}-{kwargs['object_id']}.json")
    @classmethod
    def load_all(cls):
        """
        Load playlists from local storage.
        """
        return map(cls.load_json, festune.data.list_contents("playlist"))


@dataclasses.dataclass
class FestonPlaylist(Playlist):
    """
    A playlist to be managed by the app.
    """
    year: int
    month: int

    @classmethod
    def from_api(cls, playlist_json):
        """
        Construct the object from the json API.
        """
        result = PLAYLIST_NAME_DATE_REGEX.match(playlist_json['name'])
        if not result:
            raise Error("Failed to parse playlist name: "
                        f"{playlist_json['name']}")

        try:
            year = int(result.group('year'))
            if year < 2000:
                year += 2000

            month = month_number_from(result.group('month_name'))
        except ValueError as error:
            raise Error(f"Failed to parse playlist name "
                        f"{playlist_json['name']}: {error}")

        parent = dataclasses.asdict(Playlist.from_api(playlist_json))
        return cls(year=year, month=month, **parent)

    def __lt__(self, other):
        return (self.year, self.month) < (other.year, other.month)

    def __le__(self, other):
        return (self.year, self.month) <= (other.year, other.month)

    def __eq__(self, other):
        return (self.year, self.month) == (other.year, other.month)

    def __ne__(self, other):
        return (self.year, self.month) != (other.year, other.month)

    def __gt__(self, other):
        return (self.year, self.month) > (other.year, other.month)

    def __ge__(self, other):
        return (self.year, self.month) >= (other.year, other.month)

    def __hash__(self):
        return hash((self.object_id, self.snapshot_id))


@dataclasses.dataclass
class PlaylistTrack(festune.spotify.Object):
    """
    Currently we store the minimum amount of usefull data: track id, artist(s)
    names and track name.

    ISRC is a code that uniquely identify a track, its an international
    standard.
    """
    isrc: Optional[str]
    user_id: str
    playlist_id: str
    artists: List[str]
    name: str

    @classmethod
    def from_api(cls, user_id, playlist_id, track_json):
        if track_json["type"] != "track":
            raise ValueError("Supplied json object is not a track")

        return cls(
            track_json["type"],
            track_json["id"],
            track_json.get("external_ids", {}).get("isrc"),
            user_id,
            playlist_id,
            [artist["name"] for artist in track_json["artists"]],
            track_json["name"])

    @classmethod
    def load_all(cls):
        """
        Load playlists from local storage.
        """
        return map(cls.load_json, festune.data.list_contents("track"))

    def __hash__(self):
        return hash((self.object_type, self.object_id))
