# coding: utf-8
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
