# coding: utf-8
"""
Store objects on disk.

Note that the data model is not versioned and changes in code can make the data
on disk unreadable.
"""
import dataclasses
import functools
import json
import os
import pathlib
import typing

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

    SERIALIZABLE_TYPES = frozenset((str, int, float, bool, type(None), ))

    @staticmethod
    def get_object_filename(**kwargs):
        return f"{kwargs['object_type']}.json"

    @classmethod
    def json_serializable(cls, obj):
        if isinstance(obj, dict):
            return (
                "festune-dict",
                tuple((key, cls.json_serializable(obj[key])) for key in obj)
            )

        return obj

    @staticmethod
    def from_json_serializable(obj):
        if isinstance(obj, dict):
            to_update = {}
            for key, value in obj.items():
                if not (isinstance(value, list) and value
                        and value[0] == "festune-dict"):
                    continue

                to_update[key] = dict(value[1])

            obj.update(to_update)

        return obj

    @classmethod
    @functools.lru_cache(maxsize=2, typed=True)
    def get_dict_fields(cls, with_non_serializable_keys_only=True):
        dict_fields = set()

        for field, field_type in typing.get_type_hints(cls).items():
            if getattr(field_type, "__origin__", None) is dict:
                if not with_non_serializable_keys_only:
                    dict_fields.add(field)
                    continue

                if field_type.__args__[0] not in cls.SERIALIZABLE_TYPES:
                    dict_fields.add(field)

        return dict_fields

    def save(self):
        serializable = dataclasses.asdict(self)
        filename = self.get_object_filename(**serializable)

        # We may use composite keys (tuples) in fields typed as dict, which is
        # not supported in json.
        # We transform them in tuples of (key, value) to solve the problem.
        # We don't support more complex situations yet
        for field in self.get_dict_fields():
            serializable[field] = tuple(
                tuple(item) for item in serializable[field].items())

        with open_file(filename, "w") as data_file:
            data_file.write(json.dumps(serializable))

    @classmethod
    def load_json(cls, json_str):
        """
        Load the object from the file, using :meth:`get_object_filename()`
        arguments.

        :param object_type: object type, as a string
        """
        obj = json.loads(json_str)

        # Ensure that if the type of the field is a dict, the object is a dict
        # (not a tuple of (key, value) items)
        for field in cls.get_dict_fields():
            obj[field] = dict((tuple(k), v) for k, v in obj[field])

        return cls(**obj)

    @classmethod
    def load(cls, **args):
        """
        Load the object from the file, using :meth:`get_object_filename()`
        arguments.

        :param object_type: object type, as a string
        """
        with open_file(cls.get_object_filename(**args), "r") as data_file:
            return cls.load_json(data_file.read())
