Festune 🎵
==========

Manage my Spotify playlists with a script.

This script will:
* sort my playlists
* look for duplicates in a subset of the playlists
* make a "rotating playlist" with the recently added tracks

License
-------

GPLv3

Usage
-----

Festune will import a module named ``settings``. The location of this file can
be specified with ``PYTHONPATH``, or you can put it next to the sources of the
festune package and install it in a virtualenv with ``python setup.py
develop``.

Copy ``settings_dist.py`` to ``settings.py``, set the matching settings.

Alternatively, you can create a ``settings.py`` file which imports the defaults
from ``settings_dist.py``::

    from settings_dist import *

    MY_OVERRIDEN_CONFIGURATION_KEY = ""

This file is loaded by the main scripts from the current directory, unless a
CLI option overrides its location.

When festune is installed, to log-in do:

    festune-login

The token will be stored on disk.
