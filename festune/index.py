# coding: utf-8
import collections

import festune.playlist


class PlaylistsIndex:
    """
    Index playlists by ID.

    Can be used to:
    * iterate through playlist (order is insertion order),
    * test if a playlist with same id is present,
      ``playlist in playlists`` or ``playlist_id in playlists``.
    """
    _playlist_type = festune.playlist.Playlist

    def __init__(self):
        self.by_id = dict()

    def add(self, playlist):
        self.by_id[(playlist.user_id, playlist.object_id)] = playlist

    def add_all(self, playlists):
        for playlist in playlists:
            self.add(playlist)

    def __iter__(self):
        return iter(self.by_id.values())

    def find_by_id(self, user_id, playlist_id=None):
        if not playlist_id:
            user_id, playlist_id = user_id

        return self.by_id[(user_id, playlist_id)]

    def find(self, playlist):
        return self.by_id[(playlist.user_id, playlist.object_id)]

    def __contains__(self, key):
        if isinstance(key, festune.playlist.Playlist):
            key = key.user_id, key.object_id

        return key in self.by_id

    def get_playlists_to_refresh(self, spotify):
        to_refresh = type(self)()
        for playlist in self._playlist_type.load_all_from_server(spotify):
            try:
                existing = self.find(playlist)
                if existing.snapshot_id == playlist.snapshot_id:
                    # This playlist exists on disk and both versions match
                    continue
            except KeyError:
                # Playlist seems new
                pass

            to_refresh.add(playlist)

        return to_refresh


class FestonPlaylistsIndex(PlaylistsIndex):
    _playlist_type = festune.playlist.FestonPlaylist

    def __init__(self):
        super().__init__()
        self.by_date = dict()

    def add(self, playlist):
        super().add(playlist)
        self.by_date[(playlist.year, playlist.month)] = playlist

    def __iter__(self):
        keys = sorted(self.by_date.keys())
        return iter(self.by_date[k] for k in keys)

    def reverse_iter(self):
        keys = sorted(self.by_date.keys(), reverse=True)
        return iter(self.by_date[k] for k in keys)

    def find_by_date(self, year, month):
        return self.by_date[(year, month)]


class TracksIndex:
    """
    Custom set of tracks, allows to detect duplicates.
    """
    def __init__(self):
        self.tracks_set = set()
        self.hashes_set = set()
        self.in_playlists = collections.defaultdict(set)

    def add(self, track):
        self.hashes_set.add(hash(track))
        self.tracks_set.add(track)

        self.in_playlists[hash(track)].add(
            (track.user_id, track.playlist_id))

    def add_all(self, tracks):
        for track in tracks:
            self.tracks_set.add(track)
            self.hashes_set.add(hash(track))
            self.in_playlists[hash(track)].add(
                (track.user_id, track.playlist_id))

    def playlists_of(self, track):
        return self.in_playlists[hash(track)]

    def __iter__(self):
        return iter(self.tracks_set)

    def __len__(self):
        return len(self.hashes_set)

    def __contains__(self, track):
        return hash(track) in self.hashes_set
