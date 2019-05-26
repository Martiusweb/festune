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
        playlist.save()

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
        self.tracks = {}
        self.in_playlists = collections.defaultdict(set)
        self.tracks_of_playlist = collections.defaultdict(dict)

    def add(self, track):
        """
        Add the track in the index. If the track was known, ensure the track
        has a comprehensite set of playlists.

        Return the track object stored in the index.
        """
        track_hash = hash(track)
        track_in_index = self.tracks.setdefault(track_hash, track)

        # If we knew about this track, ensure it knows about all playlists
        if track_in_index is not track:
            track_in_index.playlists.update(track.playlists)

        self.in_playlists[track_hash].update(track.playlist_ids)

        for playlist, position in track.playlists.items():
            self.tracks_of_playlist[playlist][position] = track

        track_in_index.save()
        return track_in_index

    def add_all(self, tracks):
        """
        Same as :meth:`add()` but for all tracks in the iterable ``tracks``.

        Returns an iterable of track objects stored in the index.
        """
        return set(self.add(track) for track in tracks)

    def playlists_of(self, track):
        return self.in_playlists[hash(track)]

    def tracks_of(self, playlist):
        """
        Returns the tracks of the given playlist.

        The playlist may contain holes, so it is returned as a possibly
        unsorted sequence of tuples (position, track).
        """
        if isinstance(playlist, festune.playlist.Playlist):
            playlist = (playlist.user_id, playlist.object_id)

        return self.tracks_of_playlist.get(playlist, set())

    def remove_track_from(self, track, playlist):
        if isinstance(playlist, festune.playlist.Playlist):
            playlist = (playlist.user_id, playlist.object_id)

        track_hash = hash(track)
        track = self.tracks.setdefault(track_hash, track)
        self.in_playlists[track_hash].discard(playlist)
        track.playlists.pop(playlist, None)

        self.tracks_of_playlist[playlist] = dict(
            (pos, t) for (pos, t) in self.tracks_of_playlist[playlist].items()
            if hash(t) == hash(track))

        track.save()
        return track

    def __iter__(self):
        return iter(self.tracks.values())

    def __len__(self):
        return len(self.tracks)

    def __contains__(self, track):
        return hash(track) in self.tracks


def refresh_indexes(spotify, playlists, tracks):
    """
    Refresh the indexes from the server: update playlists and tracks, and
    return a dict {playlist_id: set of tracks in the  playlist}.
    """
    refreshed_tracks = {}
    for playlist in playlists.get_playlists_to_refresh(spotify):
        playlists.add(playlist)

        old_tracks_set = tracks.tracks_of(playlist)

        new_tracks = festune.playlist.PlaylistTrack.load_from_server(
            spotify, playlist)

        if old_tracks_set:
            new_track_hashes = set(map(hash, new_tracks))

            for track in old_tracks_set:
                if hash(track) not in new_track_hashes:
                    tracks.remove_track_from(track, playlist)

        refreshed_tracks[playlist] = tracks.add_all(new_tracks)

    return refreshed_tracks
