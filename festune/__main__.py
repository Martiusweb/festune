# coding: utf-8
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
    refreshed_tracks = festune.index.refresh_indexes(
        spotify, playlists, tracks)

    duplicates = festune.index.TracksIndex()

    for track in itertools.chain.from_iterable(refreshed_tracks.values()):
        if track not in tracks:
            continue

        playlists_of_track = tracks.playlists_of(track)
        if len(playlists_of_track) > 1:
            duplicates.add(track)

    for track in duplicates:
        print(f"Track {track.artists[0]} - {track.name} is a duplicate, in:")
        for playlist in duplicates.playlists_of(track):
            print(f"\t* {playlists.find_by_id(playlist).name}")

    if not duplicates:
        print("No new duplicate found")


if __name__ == "__main__":
    main()
