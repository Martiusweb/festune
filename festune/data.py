# coding: utf-8
"""
Store objects on disk.

Note that the data model is not versioned and changes in code can make the data
on disk unreadable.
"""

import dataclasses
import json
import os
import pathlib

import settings


_DATA_DIR = pathlib.Path(settings.DATA_DIR)


def open_file(path, mode='r', **kwargs):
    """
    Open the file in the ``DATA_DIR``.

    If the file is opened in write mode, the function ensures that the parent
    directory exists.

    Arguments are the same as the standard :meth:`open()`.
    """
    is_write_mode = mode[0] in "wax" or "+" in mode
    path = get_filename(path, create_parent=is_write_mode)
    return open(path, mode, **kwargs)


def get_filename(path, create_parent=True):
    """
    Return the resolved filename of the given ``path`` in the ``DATA_DIR``.

    If ``create_parent`` is ``True``, the function ensures that the parent
    directory exists.
    """
    path = _DATA_DIR / path
    if create_parent:
        os.makedirs(path.parent, exist_ok=True)
    return path


def scan(path):
    """
    List the content of ``path``, which must be an existing directory.
    """
    path = _DATA_DIR / path
    return map(lambda p: p.relative_to(_DATA_DIR), path.iterdir())


def list_contents(path):
    """
    Iterate through ``path`` and reads the content of each file.

    If ``path`` doesn't exist, an empty iterable is returned.
    """
    path = _DATA_DIR / path
    try:
        for filename in path.iterdir():
            with open(filename, "r") as data_file:
                yield data_file.read()
    except FileNotFoundError:
        yield from tuple()


@dataclasses.dataclass
class DataObject:
    object_type: str

    @staticmethod
    def get_object_filename(**kwargs):
        return f"{kwargs['object_type']}.json"

    def save(self):
        serializable = dataclasses.asdict(self)
        filename = self.get_object_filename(**serializable)

        with open_file(filename, "w") as data_file:
            data_file.write(json.dumps(serializable))

    @classmethod
    def load_json(cls, json_str):
        """
        Load the object from the file, using :meth:`get_object_filename()`
        arguments.

        :param object_type: object type, as a string
        """
        return cls(**json.loads(json_str))

    @classmethod
    def load(cls, **args):
        """
        Load the object from the file, using :meth:`get_object_filename()`
        arguments.

        :param object_type: object type, as a string
        """
        with open_file(cls.get_object_filename(**args), "r") as data_file:
            return cls.load_json(data_file.read())
