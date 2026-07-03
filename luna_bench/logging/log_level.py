from __future__ import annotations

import logging
from enum import IntEnum


class LogLevel(IntEnum):
    """Logging levels that work where ``int`` is expected.

    Members match the ``logging`` module constants:
    ``LogLevel.DEBUG == logging.DEBUG == 10``.
    """

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

    @classmethod
    def coerce(cls, level: int | str | LogLevel, /) -> LogLevel:
        """Convert ``int``, ``str`` or ``LogLevel`` to a ``LogLevel``.

        Parameters
        ----------
        level : int | str | LogLevel
            ``LogLevel`` member, ``logging`` constant, numeric value,
            or level name like ``"DEBUG"``.

        Returns
        -------
        LogLevel
            The matching member.

        Raises
        ------
        ValueError
            If the name does not match any ``LogLevel`` member.
        """
        if isinstance(level, cls):
            return level
        if isinstance(level, str):
            return cls[level.upper()]
        return cls(level)
