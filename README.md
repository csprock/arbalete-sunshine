# Arbalete Sunlight Analysis

This repository calculates the first and last sunlit times (i.e. the first and last rays
of sunlight) hitting the terrace of the Arbalete Pub in Geneva, Switzerland. In its
initial version, the code uses the GPS coordinates (46.202836, 6.151757) and computes
solar positions based solely on the sun being above the horizon. Our long-term goal is
to extend this analysis to determine the first and last rays for all four corners of the
terrace, while eventually incorporating detailed building geometries for more advanced
shading analysis.

## Features

- **Solar Position Calculation:**  
  Uses the `pvlib` library to accurately compute the sun’s azimuth and elevation angles
  throughout the day.

- **Time Series Analysis:**  
  Generates a time series for a specified date (default is today's date) at a
  configurable interval (e.g., 10 minutes).

- **Sunlight Timing:**  
  Determines the first and last sunlit times for the terrace based on when the sun is
  above the horizon.

- **Modular Design:**  
  The project is structured into separate modules for configuration, solar calculations,
  and (future) building geometry management, making it easy to extend and maintain.

## Installation

This project requires Python 3.6+.

1. **Clone the repository:**

   ```bash
   git clone https://github.com/yourusername/arbalete-sunlight.git
   cd arbalete-sunlight
   ```

2. **Install dependencies:**

   Make sure you have [pip](https://pip.pypa.io/) installed, then run:

   ```bash
   pip install -r requirements.txt
   ```

   The `requirements.txt` should contain at least:

   ```txt
   pvlib
   pandas
   numpy
   ```

## Usage

To calculate the first and last sunlit times for today at the given coordinates, simply
run:

```bash
python src/main.py
```

This will output the first and last times when the terrace is sunlit (based on the
simple assumption that the terrace is sunlit whenever the sun is above the horizon).

## Repository Structure

```bash
arbalete-sunlight/
├── README.md              # Project overview and instructions
├── LICENSE                # License information
├── requirements.txt       # List of dependencies
├── setup.py               # Packaging configuration (optional)
├── docs/
│   └── design.md          # High-level design and future roadmap
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration: location, timezone, etc.
│   ├── solar.py           # Module to compute solar positions and determine first/last
│   │                      # sunlit times
│   ├── main.py            # Main script to run the calculation
│   └── geometry.py        # (Future) Module to define and manage building geometries
└── tests/
    ├── __init__.py
    └── test_solar.py      # Unit tests for the solar module
```

## Contributing

Contributions are welcome! If you have suggestions for improvements or find issues,
please open an issue or submit a pull request. For major changes, please discuss them
first via an issue.

## Future Plans

- **Building Geometry Integration:**  
  Develop a module (`src/geometry.py`) to import and handle detailed building geometries
  from GIS/BIM data for more precise shading analysis.

- **Multiple Terrace Corners:**  
  Extend the model to calculate the first and last sunlit times for all four corners of
  the terrace.

- **Visualization:**  
  Add visualization features to plot the sun path and shading on the terrace.

- **Extended Analysis:**  
  Enable analysis over multiple dates and produce seasonal reports.

## License

This project is licensed under the [GNU GENERAL PUBLIC LICENSE](LICENSE).
