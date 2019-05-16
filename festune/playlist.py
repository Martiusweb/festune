# coding: utf-8
import dataclasses
import re

import festune.exceptions


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


def load_all(spotify):
    """
    Load all "Feston" playlists.
    """
    playlists_json = spotify.current_user_playlists()
    feston_playlists = []

    while True:
        playlists = playlists_json['items']

        feston_playlists.extend(
            FestonPlaylist.from_api(playlist)
            for playlist in playlists
            if is_feston(playlist['name']))

        if not playlists_json['next']:
            break

        playlists_json = spotify.next(playlists_json)

    print(feston_playlists)
    return feston_playlists


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
class FestonPlaylist:
    """
    A playlist to be managed by the app.
    """
    year: int
    month: int
    name: str

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
            year = int(result.group('year')) + 2000
            month = month_number_from(result.group('month_name'))
        except ValueError as error:
            raise Error(f"Failed to parse playlist name "
                        f"{playlist_json['name']}: {error}")

        return cls(year, month, playlist_json['name'])
