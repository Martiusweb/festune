# coding: utf-8
import collections

import festune.spotify
import festune.playlist


class TracksIndex:
    """
    Custom set of tracks, allows to detect duplicates.
    """
    def __init__(self):
        self.tracks_set = set()
        self.hashes_set = set()
        self.in_playlists = collections.defaultdict(list)

    def add(self, track):
        self.hashes_set.add(hash(track))
        self.tracks_set.add(track)

        self.in_playlists[hash(track)].append(
            (track.user_id, track.playlist_id))

    def add_all(self, tracks):
        self.tracks_set.update(tracks)
        self.hashes_set.update(map(hash, tracks))

        for track in tracks:
            if track.object_id == "7BsB5WZN7V721o6gCjysJ9":
                print("added", track)

            self.in_playlists[hash(track)].append(
                (track.user_id, track.playlist_id))

    def playlists_of(self, track):
        return self.in_playlists[hash(track)]

    def __iter__(self):
        return iter(self.tracks_set)

    def __len__(self):
        return len(self.hashes_set)

    def __contains__(self, track):
        return hash(track) in self.hashes_set


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

    def find_by_date(self, year, month):
        return self.by_date[(year, month)]


def main():
    spotify = festune.spotify.get_spotify()

    playlists = FestonPlaylistsIndex()
    tracks = TracksIndex()

    playlists.add_all(festune.playlist.FestonPlaylist.load_all())

    # Check which playlists we need to refresh
    to_refresh = playlists.get_playlists_to_refresh(spotify)

    # Load all tracks, except the one to refresh
    for track in festune.playlist.PlaylistTrack.load_all():
        if track.playlist not in to_refresh:
            tracks.add(track)

    print("Found", len(tracks), "tracks")

    duplicates = False
    for playlist in to_refresh:
        playlists.add(playlist)
        playlist.save()

        print("Refreshed playlist", playlist.name)

        # Load tracks from this playlist, check that these tracks are not in
        # known tracks
        playlist_tracks = set(festune.playlist.PlaylistTrack.load_from_server(
            spotify, playlist))

        for track in playlist_tracks:
            if track in tracks:
                duplicates = True

                print(f"Duplicate track {track.artists[0]} - {track.name}"
                      f"in {playlist.name}, also found in:")
                for other_playlist in tracks.playlists_of(track):
                    print("\t*", playlists.find_by_id(other_playlist).name)
            else:
                track.save()

            tracks.add(track)

    if not duplicates:
        print("No new duplicate found")


if __name__ == "__main__":
    main()
