# coding: utf-8

import festune.spotify
import festune.playlist


def main():
    spotify = festune.spotify.get_spotify()
    for playlist in festune.playlist.load_all(spotify):
        playlist.save()

        for track in festune.playlist.load_tracks(spotify, playlist):
            track.save()


if __name__ == "__main__":
    main()
