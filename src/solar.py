"""
Module for solar position calculations and determining first/last sunlit times. Uses
pvlib to compute the sun’s position based on the configured location.

Functions:
    - get_time_series(date_str: str, freq: str = '10min') -> pd.DatetimeIndex
    - get_solar_positions(times: pd.DatetimeIndex) -> pd.DataFrame
    - get_sunlit_times(solar_positions: pd.DataFrame) -> tuple[pd.Timestamp | None,
      pd.Timestamp | None]
"""

from __future__ import annotations
from datetime import datetime
from typing import Tuple

import pandas as pd
import pvlib

from src.config import LATITUDE, LONGITUDE, TIMEZONE, DATE_FORMAT, ALTITUDE


def get_time_series(date_str: str, freq: str = "30s") -> pd.DatetimeIndex:
    """
    Generate a time series for a given date at the specified frequency.

    Args:
        date_str: A string representing the date (format defined in config).
        freq: Frequency string (default '30s') for the time intervals.

    Returns:
        A pandas DatetimeIndex covering the entire day in the configured timezone.
    """
    start = f"{date_str} 00:00:00"
    end = f"{date_str} 23:59:59"
    return pd.date_range(start=start, end=end, freq=freq, tz=TIMEZONE)


def get_solar_positions(times: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Compute solar positions for a series of times using pvlib.

    Args:
        times: A pandas DatetimeIndex representing time intervals.

    Returns:
        A DataFrame with solar position data (including 'elevation' and 'azimuth').
    """
    return pvlib.solarposition.get_solarposition(
        times, LATITUDE, LONGITUDE, altitude=ALTITUDE, method="nrel_numpy"
    )


def get_sunlit_times(
    solar_positions: pd.DataFrame,
) -> Tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """
    Determine the first and last sunlit times for the day, considering atmospheric
    refraction.

    Args:
        solar_positions: DataFrame with at least an 'elevation' column indexed by time.

    Returns:
        A tuple containing the first and last timestamps where elevation > -0.9°
        (accounting for refraction). If no sunlit period is found, returns (None, None).
    """
    # Adjust threshold: Use a slightly lower value for morning refraction sensitivity
    morning_threshold = -0.9  # More conservative for first light
    evening_threshold = -0.833  # Standard refraction correction for last light

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
    solar_pos = get_solar_positions(times)
    first_ray, last_ray = get_sunlit_times(solar_pos)
    print(f"Date: {today}")
    print("First sunlit time (first ray):", first_ray)
    print("Last sunlit time (last ray):", last_ray)
