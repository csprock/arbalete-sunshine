"""
Module for geometry-related calculations for the Arbalete Sunlight Analysis project.
Provides functionality to compute and describe the terrace borders in meters.
"""

from typing import Dict, Tuple, Union
import numpy as np
import pyproj

from src.config import TERRACE_CORNERS


def compute_border_lengths(corners: Dict[str, Tuple[float, float]]) -> Dict[str, float]:
    """
    Given a dictionary of terrace corners with keys 'NW', 'NE', 'SE', and 'SW'
    (representing the respective corners of the terrace in WGS84),
    compute the approximate lengths of the northern, eastern, southern, and
    western borders in meters.

    Args:
        corners: A dictionary mapping corner labels to (latitude, longitude) tuples.
                 Expected keys: 'NW', 'NE', 'SE', 'SW'.

    Returns:
        A dictionary with keys 'north', 'east', 'south', and 'west' containing the
        corresponding border lengths in meters.
    """
    # Initialize a geodetic calculator for the WGS84 ellipsoid
    geod = pyproj.Geod(ellps="WGS84")

    # Extract corner coordinates
    nw = corners["NW"]
    ne = corners["NE"]
    se = corners["SE"]
    sw = corners["SW"]

    # Compute borders (note: pyproj expects coordinates as (lon, lat))
    north_border = geod.inv(nw[1], nw[0], ne[1], ne[0])[2]
    east_border = geod.inv(ne[1], ne[0], se[1], se[0])[2]
    south_border = geod.inv(se[1], se[0], sw[1], sw[0])[2]
    west_border = geod.inv(sw[1], sw[0], nw[1], nw[0])[2]

    return {
        "north": abs(north_border),
        "east": abs(east_border),
        "south": abs(south_border),
        "west": abs(west_border),
    }


def describe_terrace(corners: Dict[str, Tuple[float, float]]) -> str:
    """
    Generate a descriptive string for the terrace based on its border lengths.

    Args:
        corners: A dictionary mapping corner labels to (latitude, longitude) tuples.
                 Expected keys: 'NW', 'NE', 'SE', 'SW'.

    Returns:
        A string description listing the lengths of the north, east, south, and west
        borders in meters.
    """
    lengths = compute_border_lengths(corners)
    description = (
        f"Terrace Border Lengths:\n"
        f"  North border: {lengths['north']:.2f} m\n"
        f"  East border:  {lengths['east']:.2f} m\n"
        f"  South border: {lengths['south']:.2f} m\n"
        f"  West border:  {lengths['west']:.2f} m"
    )
    return description


def shadow_bearing(azimuth: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    return (azimuth + 180) % 360


def shadow_length(solar_elevation: float, height: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
    return height / np.tan(np.radians(solar_elevation))


def translate_point(lat, long, length, bearing) -> Union[Tuple[float, float], Tuple[np.ndarray, np.ndarray]]:

    # convert to radians
    lat = np.radians(lat)
    long = np.radians(long)
    bearing = np.radians(bearing)

    # Earth radius in meters
    R = 6371000

    frac_distance = length / R

    lat2 = np.arcsin(np.sin(lat) * np.cos(frac_distance) + np.cos(lat) * np.sin(frac_distance) * np.cos(bearing))
    long2 = long + np.arctan2(np.sin(bearing) * np.sin(frac_distance) * np.cos(lat),
                              np.cos(frac_distance) - np.sin(lat) * np.sin(lat2))
    
    return np.degrees(lat2), np.degrees(long2)





if __name__ == "__main__":
    description = describe_terrace(TERRACE_CORNERS)
    print(description)
