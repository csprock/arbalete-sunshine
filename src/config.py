# src/config.py
"""
Configuration module for the Arbalete Sunlight Analysis project.
Contains global constants such as GPS coordinates, timezone, and date format.
https://map.sitg.ge.ch/app/
"""

from typing import Final

LATITUDE: Final[float] = 46.202836
LONGITUDE: Final[float] = 6.151757
ALTITUDE: Final[float] = 375.06  # Altitude in meters
TIMEZONE: Final[str] = "Europe/Zurich"
DATE_FORMAT: Final[str] = "%Y-%m-%d"
TERRACE_CORNERS: Final[dict[str, tuple[float, float]]] = {
    "NW": (46.202887, 6.151729),
    "NE": (46.202878, 6.151759),
    "SW": (46.202806, 6.151667),
    "SE": (46.202800, 6.151700),
}
