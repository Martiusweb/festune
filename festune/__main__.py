# coding: utf-8
import itertools
import sys

import festune.index
import festune.spotify
import festune.playlist

import settings


def find_new_duplicates(refreshed_tracks, tracks):
    duplicates = festune.index.TracksIndex()

    for track in itertools.chain.from_iterable(refreshed_tracks.values()):
        if track not in tracks:
            continue

        playlists_of_track = tracks.playlists_of(track)
        if len(playlists_of_track) > 1:
            duplicates.add(track)

    return duplicates


def list_last_tracks(playlists, tracks, max_nb=30):
    missing = max_nb
    last_tracks = []
    for playlist in playlists.reverse_iter():
        added = tracks.tracks_of(playlist).items()
        last_tracks.append(map(lambda t: t[1], sorted(added)[-missing:]))
        missing -= len(added)

        if missing <= 0:
            break

    return itertools.chain.from_iterable(reversed(last_tracks))


def main():
    actions = set(sys.argv)

    if not actions:
        print("You need to specify one or more actions in:", file=sys.stderr)
        print("\t* find_duplicates", file=sys.stderr)
        print("\t* update_rotating", file=sys.stderr)
        return

    spotify = festune.spotify.get_spotify()

    # Load from disk
    playlists = festune.index.FestonPlaylistsIndex()
    tracks = festune.index.TracksIndex()

    playlists.add_all(festune.playlist.FestonPlaylist.load_all())
    tracks.add_all(festune.playlist.PlaylistTrack.load_all())

    # Refresh playlists to see new changes
    refreshed_tracks = festune.index.refresh_indexes(
        spotify, playlists, tracks)

    if not refreshed_tracks:
        print("Nothing to do after refresh")

    if "find_duplicates" in actions:
        # Display duplicates
        duplicates = find_new_duplicates(
            itertools.chain.from_iterable(refreshed_tracks.values()), tracks)

        for track in duplicates:
            print(f"Track {track.artists[0]} - {track.name} is a duplicate, "
                  "in:")

            for playlist in duplicates.playlists_of(track):
                print(f"\t* {playlists.find_by_id(playlist).name}")

        if not duplicates:
            print("No new duplicate found")

    if "update_rotating" in actions:
        if not settings.ROTATING_PLAYLIST:
            print("Rotating playlist id missing from settings")
        else:
            rotating_tracks = list_last_tracks(playlists, tracks)
            spotify.user_playlist_replace_tracks(
                *settings.ROTATING_PLAYLIST,
                [track.object_id for track in rotating_tracks])

            print("Rotating playlist has been updated")


if __name__ == "__main__":
    main()
