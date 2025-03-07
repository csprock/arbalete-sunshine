"""
Module for solar position calculations and determining first/last sunlit times. Uses
pvlib to compute the sun’s position based on the configured location.

Functions:
    - get_time_series(date_str: str, freq: str = '30s') -> pd.DatetimeIndex
    - get_solar_positions(times: pd.DatetimeIndex, latitude: float = LATITUDE,
      longitude: float = LONGITUDE, altitude: float = ALTITUDE) -> pd.DataFrame
    - get_sunlit_times(solar_positions: pd.DataFrame,
      morning_threshold: float = -0.9, evening_threshold: float = -0.833)
      -> tuple[pd.Timestamp | None, pd.Timestamp | None]
"""

from __future__ import annotations
from datetime import datetime
from typing import Tuple

import pandas as pd
import pvlib

from src.config import (
    LATITUDE,
    LONGITUDE,
    TIMEZONE,
    DATE_FORMAT,
    ALTITUDE,
    TERRACE_CORNERS,
)


def get_time_series(date_str: str, freq: str = "30s") -> pd.DatetimeIndex:
    """
    Generate a time series for a given date at the specified frequency.

    Args:
        - date_str: A string representing the date (format defined in config).
        - freq: Frequency string (default '30s') for the time intervals.

    Returns:
        A pandas DatetimeIndex covering the entire day in the configured timezone.
    """
    start = f"{date_str} 00:00:00"
    end = f"{date_str} 23:59:59"
    return pd.date_range(start=start, end=end, freq=freq, tz=TIMEZONE)


def get_solar_positions(
    times: pd.DatetimeIndex,
    latitude: float = LATITUDE,
    longitude: float = LONGITUDE,
    altitude: float = ALTITUDE,
) -> pd.DataFrame:
    """
    Compute solar positions for a series of times using pvlib.

    Args:
        - times: A pandas DatetimeIndex representing time intervals.
        - latitude: Latitude of the location.
        - longitude: Longitude of the location.
        - altitude: Altitude of the location in meters.

    Returns:
        A DataFrame with solar position data (including 'elevation' and 'azimuth').
    """
    return pvlib.solarposition.get_solarposition(
        times, latitude, longitude, altitude=altitude, method="nrel_numpy"
    )


def get_sunlit_times(
    solar_positions: pd.DataFrame,
    morning_threshold: float = -0.9,
    evening_threshold: float = -0.833,
) -> Tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """
    Determine the first and last sunlit times for the day, considering atmospheric
    refraction.

    Args:
        - solar_positions: DataFrame with at least an 'elevation' column indexed by
          time.
        - morning_threshold: Elevation threshold for determining the first sunlit time.
        - evening_threshold: Elevation threshold for determining the last sunlit time.

    Returns:
        A tuple containing the first and last timestamps where elevation > threshold. If
        no sunlit period is found, returns (None, None).

    Raises:
        ValueError: If 'elevation' column is not present in the solar_positions
        DataFrame.
    """
    if "elevation" not in solar_positions.columns:
        raise ValueError(
            "Solar positions DataFrame must contain an 'elevation' column."
        )

    # Find first sunlit time (using morning threshold)
    first_sunlit_df = solar_positions[solar_positions["elevation"] > morning_threshold]
    first_ray = first_sunlit_df.index[0] if not first_sunlit_df.empty else None

    # Find last sunlit time (using evening threshold)
    last_sunlit_df = solar_positions[solar_positions["elevation"] > evening_threshold]
    last_ray = last_sunlit_df.index[-1] if not last_sunlit_df.empty else None

    return first_ray, last_ray


if __name__ == "__main__":
    # For testing purposes: run the calculations for today's date.
    today = datetime.now().strftime(DATE_FORMAT)
    times = get_time_series(today)

    # Test using the default location from config.
    solar_pos_default = get_solar_positions(times)
    first_ray_default, last_ray_default = get_sunlit_times(solar_pos_default)
    print("Default location (from config):")
    print("  First sunlit time:", first_ray_default)
    print("  Last sunlit time:", last_ray_default)

    print("\nTerrace Corners Sunlit Times:")
    for corner, (lat, lon) in TERRACE_CORNERS.items():
        solar_pos_corner = get_solar_positions(
            times, latitude=lat, longitude=lon, altitude=ALTITUDE
        )
        first_ray, last_ray = get_sunlit_times(solar_pos_corner)
        print(
            f"  {corner}: First sunlit time: {first_ray}, Last sunlit time: {last_ray}"
        )
