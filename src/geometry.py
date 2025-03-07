"""
Module for geometry-related calculations for the Arbalete Sunlight Analysis project.
Provides functionality to compute and describe the terrace borders in meters.
"""

from typing import Dict, Tuple
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


if __name__ == "__main__":
    description = describe_terrace(TERRACE_CORNERS)
    print(description)
