"""
Module for shading analysis and basic 3D building integration for the Arbalete Sunlight
Analysis project.

This module:
  1. Creates 2D footprints for the floor, the terrace, and a placeholder building.
  2. Extrudes each 2D shape to its specified height:
      - Floor: a thin, large rectangle (for context).
      - Terrace: defined by the terrace corners (extruded 1 m high).
      - Building: a fixed rectangle (81 m long southward, 15 m wide westward, 18 m high)
         with its northeast ground–corner flush with the terrace’s northwest corner and
         rotated to match the terrace edge.
  3. Applies small vertical offsets (≈1 cm) between shapes to avoid z-fighting.
  4. Computes the shadow–adjusted last sunlit time.
  5. Visualizes the scene with colored elements and a sun ray.

Colors:
  - Floor: Gray ([128, 128, 128, 255])
  - Terrace: Red ([255, 0, 0, 255])
  - Building: Blue ([0, 0, 255, 255])
  - Terrace center marker: White ([255, 255, 255, 255])
  - Sun ray: Yellow ([255, 255, 0, 255])

Note: This module uses functions from src.config and src.solar.
"""

import numpy as np
import pandas as pd
import trimesh
import pyproj
from datetime import datetime
from shapely.geometry import Polygon, box
from shapely.affinity import rotate, translate

from src.config import DATE_FORMAT, TERRACE_CORNERS
from src.solar import get_time_series, get_solar_positions


def set_vertex_color(mesh: trimesh.Trimesh, color: list[int]) -> None:
    """
    Force a mesh to use a single vertex color.

    Args:
        mesh: A trimesh.Trimesh object.
        color: A list [R, G, B, A] (0-255).
    """
    mesh.visual.vertex_colors = np.tile(color, (len(mesh.vertices), 1))


def latlon_to_utm(lon: float, lat: float) -> tuple[float, float]:
    """
    Convert WGS84 (lon, lat) to UTM (meters). Here we use EPSG:32632 (appropriate for
    Geneva).
    """
    transformer = pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32632", always_xy=True)
    x, y = transformer.transform(lon, lat)
    return x, y


def get_terrace_center(corners: dict[str, tuple[float, float]]) -> np.ndarray:
    """
    Compute the terrace center (ground-level) in UTM coordinates.
    """
    xs, ys = [], []
    for corner in corners.values():
        x, y = latlon_to_utm(corner[1], corner[0])
        xs.append(x)
        ys.append(y)
    return np.array([np.mean(xs), np.mean(ys), 0.0])


def create_terrace_polygon(corners: dict[str, tuple[float, float]]) -> Polygon:
    """
    Create a 2D polygon for the terrace footprint from the four corners.
    The order is assumed to be: NW, NE, SE, SW.
    """
    order = ["NW", "NE", "SE", "SW"]
    points = []
    for key in order:
        lat, lon = corners[key]
        x, y = latlon_to_utm(lon, lat)
        points.append((x, y))
    return Polygon(points)


def create_terrace_extrusion(
    corners: dict[str, tuple[float, float]], height: float = 1.0
) -> tuple[trimesh.Trimesh, Polygon]:
    """
    Create the terrace 2D polygon and extrude it to the given height.

    Returns:
        A tuple (terrace_mesh, terrace_polygon)
    """
    terrace_poly = create_terrace_polygon(corners)
    terrace_mesh = trimesh.creation.extrude_polygon(terrace_poly, height=height)
    # Raise the terrace by 1 cm to separate it from the floor.
    terrace_mesh.apply_translation([0, 0, 0.01])
    set_vertex_color(terrace_mesh, [255, 0, 0, 255])  # Red
    return terrace_mesh, terrace_poly


def create_floor(
    terrace_polygon: Polygon, margin: float = 10.0, thickness: float = 0.1
) -> trimesh.Trimesh:
    """
    Create a floor footprint by taking the bounding box of the terrace polygon,
    enlarging it by a margin, and extruding it to a small thickness.
    Then shift it downward by 1 cm to separate it from the terrace.
    """
    minx, miny, maxx, maxy = terrace_polygon.bounds
    floor_poly = box(minx - margin, miny - margin, maxx + margin, maxy + margin)
    floor_mesh = trimesh.creation.extrude_polygon(floor_poly, height=thickness)
    # By default, floor_mesh has its top at z = 0; shift it down by an extra 0.01 m.
    floor_mesh.apply_translation([0, 0, -0.01])
    set_vertex_color(floor_mesh, [128, 128, 128, 255])  # Gray
    return floor_mesh


def create_building_polygon(
    corners: dict[str, tuple[float, float]], length: float = 81.0, width: float = 15.0
) -> Polygon:
    """
    Create a 2D polygon for the building footprint.

    The building is defined so that its northeast (NE) corner at ground level is exactly
    the terrace's northwest (NW) point. Then the footprint extends:
      - Southward by `length` meters.
      - Westward by `width` meters.

    Returns a shapely Polygon.
    """
    # Get terrace NW point in UTM (as a 2D point).
    p_NW = np.array(latlon_to_utm(TERRACE_CORNERS["NW"][1], TERRACE_CORNERS["NW"][0]))
    E, N = p_NW  # Easting, Northing
    building_poly = Polygon(
        [
            (E, N),  # NE corner
            (E, N - length),  # SE corner
            (E - width, N - length),  # SW corner
            (E - width, N),  # NW corner
        ]
    )
    return building_poly


def create_building_extrusion(
    corners: dict[str, tuple[float, float]],
    length: float = 81.0,
    width: float = 15.0,
    height: float = 18.0,
) -> trimesh.Trimesh:
    """
    Create the building 2D footprint (using the terrace NW as reference), rotate it to
    match the terrace's top edge orientation, and extrude it to the specified height.

    In local building coordinates the footprint is defined as:
       - NE: (0, 0)
       - SE: (0, -length)
       - SW: (-width, -length)
       - NW: (-width, 0)
    This footprint is then rotated by the angle of the terrace's top border (from NW to
    NE) and translated so that its NE corner coincides with the terrace's NW point.
    """
    # Get terrace NW and NE points in UTM.
    p_NW = np.array(latlon_to_utm(corners["NW"][1], corners["NW"][0]))  # 2D point
    p_NE = np.array(latlon_to_utm(corners["NE"][1], corners["NE"][0]))  # 2D point

    # Compute the angle (in radians) of the terrace top border (from NW to NE).
    angle = np.arctan2(p_NE[1] - p_NW[1], p_NE[0] - p_NW[0])

    # Define building footprint in local coordinates.
    building_local = Polygon(
        [
            (0, 0),  # NE corner
            (0, -length),  # SE corner
            (-width, -length),  # SW corner
            (-width, 0),  # NW corner
        ]
    )

    # Rotate the building footprint by the terrace's top edge angle.
    building_rotated = rotate(building_local, angle, origin=(0, 0), use_radians=True)
    # Translate so that the building's NE corner (still at (0,0)) is at the terrace's NW
    # point.
    building_translated = translate(building_rotated, xoff=p_NW[0], yoff=p_NW[1])
    building_mesh = trimesh.creation.extrude_polygon(building_translated, height=height)
    # Raise the building by 0.02 m to separate it from the terrace.
    building_mesh.apply_translation([0, 0, 0.02])
    set_vertex_color(building_mesh, [0, 0, 255, 255])  # Blue
    return building_mesh


def sun_direction_vector(azimuth: float, elevation: float) -> np.ndarray:
    """
    Compute the sun direction unit vector from the given azimuth and elevation (in
    degrees). Uses the convention: x = east, y = north, z = up.
    """
    az_rad = np.radians(azimuth)
    el_rad = np.radians(elevation)
    cos_el = np.cos(el_rad)
    x = cos_el * np.sin(az_rad)
    y = cos_el * np.cos(az_rad)
    z = np.sin(el_rad)
    vec = np.array([x, y, z])
    norm = np.linalg.norm(vec)
    return vec if norm == 0 else vec / norm


def is_terrace_sunlit(
    terrace_center: np.ndarray, sun_dir: np.ndarray, building: trimesh.Trimesh
) -> bool:
    """
    Cast a ray from a point slightly above the terrace center in the sun direction.
    Return True if the ray does not intersect the building.
    """
    origin = terrace_center.copy()
    origin[2] += 1.0  # elevate by 1 m to simulate sensor height
    locations = building.ray.intersects_location(
        ray_origins=[origin], ray_directions=[sun_dir]
    )[0]
    return len(locations) == 0


def get_shadow_adjusted_last_sunray_time(
    times: pd.DatetimeIndex,
    solar_positions: pd.DataFrame,
    terrace_center: np.ndarray,
    building: trimesh.Trimesh,
    evening_threshold: float = -0.833,
) -> pd.Timestamp | None:
    """
    Iterate backward over times (where sun elevation is above the threshold) and return
    the last time at which the terrace is sunlit (i.e. the ray from the terrace center
    does not hit the building).
    """
    valid = solar_positions[solar_positions["elevation"] > evening_threshold]
    if valid.empty:
        return None
    for t in valid.index[::-1]:
        pos = valid.loc[t]
        sun_dir = sun_direction_vector(pos["azimuth"], pos["elevation"])
        if is_terrace_sunlit(terrace_center, sun_dir, building):
            return t
    return None


def visualize_scene(
    terrace_center: np.ndarray,
    building: trimesh.Trimesh,
    terrace_mesh: trimesh.Trimesh,
    floor: trimesh.Trimesh,
    sun_dir: np.ndarray | None = None,
    ray_length: float = 50.0,
    viewer: str = "gl",
) -> None:
    """
    Create a scene with the floor, the extruded terrace, the building, a marker at the
    terrace center, and optionally a sun ray.

    Shapes are separated by a small vertical offset to avoid collisions. Lighting is
    disabled to show flat colors.
    """
    scene = trimesh.Scene()
    scene.add_geometry(floor)
    scene.add_geometry(terrace_mesh)
    scene.add_geometry(building)

    # Add a sphere at the terrace center.
    sphere = trimesh.creation.icosphere(radius=1.0)
    sphere.apply_translation(terrace_center)
    # Raise the sphere slightly (1 cm) to avoid collisions.
    sphere.apply_translation([0, 0, 0.01])
    set_vertex_color(sphere, [255, 255, 255, 255])  # White
    scene.add_geometry(sphere)

    # If a sun direction is provided, add a ray in yellow.
    if sun_dir is not None:
        origin = terrace_center.copy()
        origin[2] += 1.0  # start the ray above the terrace center
        ray_end = origin + sun_dir * ray_length
        ray_path = trimesh.load_path(np.array([origin, ray_end]))
        # For a Path3D object, assign colors per entity.
        ray_path.colors = np.tile([255, 255, 0, 255], (len(ray_path.entities), 1))
        scene.add_geometry(ray_path)

    scene.show(lighting=False, viewer=viewer)


def main(viewer: str = "gl") -> None:
    today = datetime.now().strftime(DATE_FORMAT)
    times = get_time_series(today, freq="30s")
    solar_pos = get_solar_positions(times)

    terrace_center = get_terrace_center(TERRACE_CORNERS)

    # Create the building footprint in 2D and extrude it.
    building = create_building_extrusion(
        TERRACE_CORNERS, length=81.0, width=15.0, height=18.0
    )

    # Create the terrace from its 2D footprint and extrude it to 1 m.
    terrace_mesh, terrace_poly = create_terrace_extrusion(TERRACE_CORNERS, height=1.0)

    # Create the floor by enlarging the terrace bounding box and extruding to 0.1 m.
    floor = create_floor(terrace_poly, margin=10.0, thickness=0.1)

    last_sunray_time = get_shadow_adjusted_last_sunray_time(
        times, solar_pos, terrace_center, building
    )
    print("Shadow-adjusted last sunlit time:", last_sunray_time)

    sun_dir = None
    if last_sunray_time is not None:
        pos = solar_pos.loc[last_sunray_time]
        sun_dir = sun_direction_vector(pos["azimuth"], pos["elevation"])

    visualize_scene(
        terrace_center, building, terrace_mesh, floor, sun_dir, ray_length=50.0, viewer=viewer
    )


if __name__ == "__main__":
    today = datetime.now().strftime(DATE_FORMAT)
    times = get_time_series(today, freq="30s")
    solar_pos = get_solar_positions(times)

    terrace_center = get_terrace_center(TERRACE_CORNERS)

    # Create the building footprint in 2D and extrude it.
    building = create_building_extrusion(
        TERRACE_CORNERS, lengthvi=81.0, width=15.0, height=18.0
    )

    # Create the terrace from its 2D footprint and extrude it to 1 m.
    terrace_mesh, terrace_poly = create_terrace_extrusion(TERRACE_CORNERS, height=1.0)

    # Create the floor by enlarging the terrace bounding box and extruding to 0.1 m.
    floor = create_floor(terrace_poly, margin=10.0, thickness=0.1)

    last_sunray_time = get_shadow_adjusted_last_sunray_time(
        times, solar_pos, terrace_center, building
    )
    print("Shadow-adjusted last sunlit time:", last_sunray_time)

    sun_dir = None
    if last_sunray_time is not None:
        pos = solar_pos.loc[last_sunray_time]
        sun_dir = sun_direction_vector(pos["azimuth"], pos["elevation"])

    visualize_scene(
        terrace_center, building, terrace_mesh, floor, sun_dir, ray_length=50.0
    )