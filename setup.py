# coding: utf-8

def get_args():
    return {
        "name": "festune",
        "packages": ["festune"],
    }


if __name__ == "__main__":
    from setuptools import setup
    setup(**get_args())
