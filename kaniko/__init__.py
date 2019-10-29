from kaniko.kaniko import KanikoSnapshotMode, KanikoVerbosity, KanikoBuildException, Kaniko

__ALL__ = [
    # Enums
    KanikoSnapshotMode, KanikoVerbosity,

    # Exceptions
    KanikoBuildException,

    # Kaniko
    Kaniko,
]

VERSION = (1, 0, 0)

__title__ = 'pykaniko'
__author__ = 'Maksunov Artem'
__email__ = 'maksunov@skbkontur.ru'
__copyright__ = 'Copyright (c) 2019 Maksunov Artem, Deys Timofey'
__license__ = 'Apache License 2.0'
__url__ = 'https://github.com/nxexox/pykaniko'
__version__ = '.'.join(map(str, VERSION))
