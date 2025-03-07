# src/config.py
"""
Configuration module for the Arbalete Sunlight Analysis project.
Contains global constants such as GPS coordinates, timezone, and date format.
"""

from typing import Final

LATITUDE: Final[float] = 46.202836
LONGITUDE: Final[float] = 6.151757
ALTITUDE: Final[float] = 386.0  # Altitude in meters
TIMEZONE: Final[str] = "Europe/Zurich"
DATE_FORMAT: Final[str] = "%Y-%m-%d"
