# coding: utf-8
import collections
import itertools

import festune.index
import festune.spotify
import festune.playlist


def main():
    spotify = festune.spotify.get_spotify()

    # Load from disk
    playlists = festune.index.FestonPlaylistsIndex()
    tracks = festune.index.TracksIndex()

    playlists.add_all(festune.playlist.FestonPlaylist.load_all())
    tracks.add_all(festune.playlist.PlaylistTrack.load_all())

    # Refresh playlists to see new changes
    refreshed_tracks = {}
    for playlist in playlists.get_playlists_to_refresh(spotify):
        playlists.add(playlist)
        playlist.save()
        print("Refreshed playlist", playlist.name)

        refreshed_tracks[playlist] = set(
            festune.playlist.PlaylistTrack.load_from_server(spotify, playlist))

        for track in refreshed_tracks[playlist]:
            tracks.add(track)
            track.save()

    # From this stable view of the world, look for duplicates in refreshed
    # playlists
    # {track: [other playlist, ...]}
    duplicates = collections.defaultdict(set)

    for track in itertools.chain.from_iterable(refreshed_tracks.values()):
        print(track)
        if track not in tracks:
            continue

        playlists_of_track = tracks.playlists_of(track)
        if len(playlists_of_track) > 1:
            duplicates[track] = playlists_of_track

    for track, playlists_of_track in duplicates.items():
        print(f"Track {track.artists[0]} - {track.name} is a duplicate, in:")
        for playlist in playlists_of_track:
            print(f"\t* {playlists.find_by_id(playlist).name}")


if __name__ == "__main__":
    main()
