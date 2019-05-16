# coding: utf-8

import festune.spotify
import festune.playlist


def main():
    spotify = festune.spotify.get_spotify()
    festune.playlist.load_all(spotify)


if __name__ == "__main__":
    main()
