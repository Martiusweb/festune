# coding: utf-8

import festune.auth
import festune.playlist


def main():
    spotify = festune.auth.get_spotify()
    festune.playlist.load_all(spotify)


if __name__ == "__main__":
    main()
