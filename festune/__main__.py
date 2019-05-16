# coding: utf-8

import festune.spotify
import festune.playlist


def main():
    spotify = festune.spotify.get_spotify()

    all_tracks = set()
    duplicates = False
    for playlist in festune.playlist.load_all(spotify):
        # playlist.save()

        for track in festune.playlist.load_tracks(spotify, playlist):
            if track in all_tracks:
                duplicates = True
                print(f"Duplicate track {track.name} in {playlist.name}")

            all_tracks.add(track)
            # track.save()

    if not duplicates:
        print("No duplicate found")


if __name__ == "__main__":
    main()
