# Design and Roadmap

## Project Overview

The goal of this project is to calculate the first and last sunlit times (i.e. the times when the first and last sunrays hit) at the terrace of the Arbalete Pub in Geneva. Initially, the calculations are based solely on the terrace's GPS coordinates (latitude and longitude) and the sun's elevation (i.e., when the sun is above the horizon). The ultimate objective is to extend this functionality to determine the first and last sunlit times for all four corners of the terrace while incorporating detailed building geometries for accurate shading analysis.

## High-Level Architecture

The project is organized into modular components that facilitate both maintainability and scalability. The key modules are:

- **Configuration Module (`src/config.py`):**  
  Stores global parameters such as the terrace's GPS coordinates, timezone, and date format. This centralizes settings for easy updates.

- **Solar Calculation Module (`src/solar.py`):**  
  Uses the `pvlib` library to compute solar positions (azimuth and elevation) throughout the day. It provides functions to generate a time series for a given date, compute the solar position, and determine the first and last times when the terrace is sunlit (assuming the terrace is sunlit when the sun is above the horizon).

- **Main Application (`src/main.py`):**  
  Acts as the entry point to run the calculations. This script ties together the configuration and solar modules and will eventually handle multiple terrace corners.

- **Geometry Module (`src/geometry.py`):**  
  *Future development:* This module will manage building geometries (using GIS, BIM data, or simplified primitives) and perform ray-casting to account for shading effects.

- **Testing (`tests/`):**  
  Contains unit tests (e.g., for solar calculations) to ensure each module works as expected.

- **Documentation (`docs/`):**  
  This directory contains design documents, roadmaps, and other documentation to aid in project understanding and future enhancements.

## Module Breakdown and Interactions

1. **src/config.py**  
   - Contains constants like `LATITUDE`, `LONGITUDE`, `TIMEZONE`, and `DATE_FORMAT`.

2. **src/solar.py**  
   - **get_time_series(date_str, freq):** Generates a pandas DatetimeIndex covering the entire day at a given frequency.  
   - **get_solar_positions(times):** Computes solar positions using the `pvlib` library.  
   - **get_sunlit_times(solar_positions):** Filters solar position data to find the first and last timestamps when the sun's elevation is above zero.

3. **src/main.py**  
   - Calls functions from `solar.py` using configuration values from `config.py` to compute and display the sunlit times for the terrace.

4. **src/geometry.py**  
   - *Planned:* Will include functions/classes for representing building geometries and performing intersection tests (ray-casting) to determine shading.

## Future Roadmap

### Phase 1: Basic Solar Calculation (Current)

- **Complete and test** the solar calculation module (`src/solar.py`) to compute first and last sunlit times based solely on solar geometry.
- **Establish** a solid configuration system using `src/config.py`.

### Phase 2: Handling Multiple Terrace Corners

- **Extend `src/main.py`:** Modify the main script to calculate sunlit times for each of the four corners of the terrace.
- **Parameterize Corner Coordinates:** Update the configuration to support multiple points.

### Phase 3: Building Geometry and Shading Analysis

- **Develop `src/geometry.py`:**  
  - Import and manage building geometry data (e.g., using GIS/BIM data or simple geometric primitives).  
  - Implement ray-casting algorithms to check whether the sun's rays are obstructed by surrounding buildings.
- **Integrate Shading Analysis:** Combine solar calculations with building geometry to refine the sunlit time calculations.

### Phase 4: Visualization and Reporting

- **Visualization Tools:** Develop scripts or use existing libraries (e.g., matplotlib) to generate sun path diagrams and shading maps.
- **Reporting:** Create a module to export or display detailed results and seasonal analyses.

## Design Considerations

- **Modularity:** Each functionality is encapsulated within its own module to ease maintenance and testing.
- **Testability:** Unit tests in the `tests/` directory will ensure that changes do not break the core functionality.
- **Extensibility:** The current design is intended as a foundation that can be expanded with additional features (such as full building shading analysis) in later phases.
- **Compliance:** We aim to adhere to best practices, including PEP8 style guidelines, type annotations, and automated formatting using tools like Black and Flake8.

## Dependencies and Tools

- **pvlib:** Used for accurate solar position calculations.
- **pandas & numpy:** For time series and numerical computations.
- **Python 3.6+:** The minimum version required for type annotations and other modern Python features.

## Testing Strategy

- **Unit Tests:** Tests will be written for key functions in `src/solar.py` (and later `src/geometry.py`) to ensure correct functionality.
- **Continuous Integration:** Future plans include setting up CI (using GitHub Actions or Travis CI) to automatically run tests on each commit.

---

This design document will evolve as new features and modules are developed. Feedback and contributions are welcome as we refine the architecture to meet production standards.
