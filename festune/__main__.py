# coding: utf-8
import collections

import festune.spotify
import festune.playlist


class KnownTracks:
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
    def __init__(self):
        self.by_date = dict()
        self.by_id = dict()

    def add(self, playlist):
        self.by_date[(playlist.year, playlist.month)] = playlist
        self.by_id[(playlist.user_id, playlist.object_id)] = playlist

    def add_all(self, playlists):
        for playlist in playlists:
            self.add(playlist)

    def __iter__(self):
        keys = sorted(self.by_date.keys())
        return iter(self.by_date[k] for k in keys)

    def find_by_date(self, year, month):
        return self.by_date[(year, month)]

    def find_by_id(self, user_id, playlist_id=None):
        if not playlist_id:
            user_id, playlist_id = user_id

        return self.by_id[(user_id, playlist_id)]


def main():
    spotify = festune.spotify.get_spotify()

    playlists = PlaylistsIndex()
    playlists.add_all(festune.playlist.FestonPlaylist.load_all())

    # Check which playlists we need to refresh
    to_refresh = set(
        (pl.user_id, pl.object_id)
        for pl in festune.playlist.load_all_from_server(spotify)
        if pl not in playlists
    )

    # Load all tracks, except the one to refresh
    tracks = KnownTracks()
    for track in festune.playlist.PlaylistTrack.load_all():
        if (track.user_id, track.playlist_id) not in to_refresh:
            tracks.add(track)

    print("Found", len(tracks), "tracks")

    duplicates = False
    for playlist in to_refresh:
        playlist = festune.playlist.load_from_server(spotify, *playlist)
        playlists.add(playlist)
        print("Refreshed playlist", playlist.name)

        playlist.save()

        # Load tracks from this playlist, check that these tracks are not in
        # known tracks
        playlist_tracks = set(festune.playlist.load_tracks_from_server(
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
        print("No duplicate found")


if __name__ == "__main__":
    main()
