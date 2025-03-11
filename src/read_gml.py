"""
read_gml.py

Module to read a CityGML 2.0 file containing building data (with EGID), print out all
unique EGIDs, and then process one building to create a 3D mesh. Additionally, the
module computes and prints the building’s EGID and its centroid location in latitude and
longitude.

Workflow:
  1. Parse the CityGML file using lxml.
  2. Find all building elements.
  3. Extract and print unique EGID values.
  4. Select the first building element.
  5. Compute its centroid from the union of its surfaces and transform it to WGS84.
  6. Extract its surfaces (<gml:Polygon>), triangulate each surface, and assemble them
     into a Trimesh mesh.
  7. Export the final mesh as an OBJ file.

Usage:
  Modify FILE_PATH as needed, then run:
      python -m src.read_gml
"""

import os
from lxml import etree
from shapely.geometry import Polygon
from shapely.ops import unary_union, triangulate
import trimesh
import numpy as np
from pyproj import Transformer

# Define the namespaces used in CityGML 2.0.
NSMAP = {
    "gml": "http://www.opengis.net/gml",
    "bldg": "http://www.opengis.net/citygml/building/2.0",
    "core": "http://www.opengis.net/citygml/2.0",
}

# Path to the CityGML file.
FILE_PATH = os.path.join(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "data",
    "swissBUILDINGS3D_3-0_1091-23.gml",
)
# Set target EGID (adjust as needed).
TARGET_EGID = "1010180"

# Define source and target CRS.
# Assuming the CityGML file is in Swiss LV95 (EPSG:2056) and we want WGS84 (EPSG:4326)
SOURCE_EPSG = "EPSG:2056"
TARGET_EPSG = "EPSG:4326"


def parse_citygml(file_path):
    """Parse the CityGML file and return the XML tree."""
    tree = etree.parse(file_path)
    return tree


def find_all_buildings(tree):
    """
    Find all building elements.
    Returns a list of building elements.
    """
    buildings = tree.xpath(".//bldg:Building", namespaces=NSMAP)
    return buildings


def extract_egid(building_elem):
    """
    Extract the EGID from a building element.
    Assumes the EGID is stored in a <bldg:EGID> element.
    """
    egid_elem = building_elem.find(".//bldg:EGID", namespaces=NSMAP)
    if egid_elem is not None and egid_elem.text:
        return egid_elem.text.strip()
    return None


def print_unique_egids(buildings):
    """Print all unique EGIDs from the list of building elements."""
    egids = set()
    for b in buildings:
        egid = extract_egid(b)
        if egid:
            egids.add(egid)
    print("Unique EGIDs found in the file:")
    for egid in sorted(egids):
        print("  ", egid)
    return egids


def get_building_location(building_elem):
    """
    Compute the centroid (x,y) of a building element (by unioning all its surfaces)
    and transform that coordinate from the source CRS (assumed EPSG:2056) to WGS84.
    Returns (lat, lon).
    """
    # Extract all polygon surfaces
    polygons = building_elem.xpath(".//gml:Polygon", namespaces=NSMAP)
    polys = []
    for poly_elem in polygons:
        posList_elem = poly_elem.find(".//gml:posList", namespaces=NSMAP)
        if posList_elem is None or posList_elem.text is None:
            continue
        coords_str = posList_elem.text.strip()
        coords = [float(v) for v in coords_str.split()]
        pts = []
        for i in range(0, len(coords), 3):
            pts.append((coords[i], coords[i + 1], coords[i + 2]))
        if pts:
            # Use only x,y for footprint.
            xy = [(pt[0], pt[1]) for pt in pts]
            try:
                poly = Polygon(xy)
                if not poly.is_empty:
                    polys.append(poly)
            except Exception as e:
                print("Error creating polygon:", e)
    if not polys:
        return None
    union_poly = unary_union(polys)
    centroid = union_poly.centroid
    # Transform from SOURCE_EPSG to WGS84.
    transformer = Transformer.from_crs(SOURCE_EPSG, TARGET_EPSG, always_xy=True)
    lon, lat = transformer.transform(centroid.x, centroid.y)
    return lat, lon


def extract_building_surfaces(building_elem):
    """
    Extract all gml:Polygon elements representing surfaces from a building element.
    """
    polygons = building_elem.findall(".//gml:Polygon", namespaces=NSMAP)
    return polygons


def parse_polygon(polygon_elem):
    """
    Extract the coordinate list from a gml:Polygon element.
    Returns a list of (x,y,z) tuples.
    """
    posList_elem = polygon_elem.find(".//gml:posList", namespaces=NSMAP)
    if posList_elem is None or posList_elem.text is None:
        return None
    coords_str = posList_elem.text.strip()
    coords = [float(v) for v in coords_str.split()]
    pts = []
    for i in range(0, len(coords), 3):
        pts.append((coords[i], coords[i + 1], coords[i + 2]))
    return pts


def triangulate_surface(points):
    """
    Given a list of 3D points for a polygon, project to 2D (x,y), triangulate the 2D
    polygon, and reattach an average z-value.
    Returns a list of triangles (each triangle is a list of three (x,y,z) tuples).
    """
    pts_2d = [(x, y) for (x, y, z) in points]
    poly = Polygon(pts_2d)
    triangles = triangulate(poly)
    avg_z = np.mean([pt[2] for pt in points])
    tri_list = []
    for tri in triangles:
        coords = list(tri.exterior.coords)[:-1]
        tri_list.append([(x, y, avg_z) for (x, y) in coords])
    return tri_list


def build_building_mesh(building_elem):
    """
    From a building element, extract all surface polygons, triangulate them, and
    assemble a Trimesh mesh.
    """
    polygons = extract_building_surfaces(building_elem)
    if not polygons:
        raise ValueError("No polygons found in building element.")
    all_triangles = []
    for poly_elem in polygons:
        pts = parse_polygon(poly_elem)
        if pts is None or len(pts) < 3:
            continue
        try:
            tris = triangulate_surface(pts)
            all_triangles.extend(tris)
        except Exception as e:
            print("Triangulation error:", e)
    vertices = []
    faces = []
    vertex_map = {}

    def add_vertex(pt):
        key = (round(pt[0], 6), round(pt[1], 6), round(pt[2], 6))
        if key in vertex_map:
            return vertex_map[key]
        index = len(vertices)
        vertices.append(pt)
        vertex_map[key] = index
        return index

    for tri in all_triangles:
        face = [add_vertex(pt) for pt in tri]
        if len(face) == 3:
            faces.append(face)
    if not vertices or not faces:
        raise ValueError("No valid triangles generated.")
    mesh = trimesh.Trimesh(
        vertices=np.array(vertices), faces=np.array(faces), process=True
    )
    return mesh


if __name__ == "__main__":
    print("Parsing CityGML file...")
    tree = parse_citygml(FILE_PATH)
    buildings = tree.xpath(".//bldg:Building", namespaces=NSMAP)
    if not buildings:
        print("No building elements found.")
        exit(1)
    print(f"Found {len(buildings)} building elements.")
    unique_egids = set()
    for b in buildings:
        egid = extract_egid(b)
        if egid:
            unique_egids.add(egid)
    print("Unique EGIDs in file:")
    for egid in sorted(unique_egids):
        print("  ", egid)

    # For this example, use the first building element.
    building_elem = buildings[0]
    egid = extract_egid(building_elem)
    print(f"Using building with EGID: {egid if egid else 'None'}")

    location = get_building_location(building_elem)
    if location:
        print(f"Building centroid (lat, lon): {location}")
    else:
        print("Could not compute building location.")

    try:
        building_mesh = build_building_mesh(building_elem)
    except Exception as e:
        print("Failed to build building mesh:", e)
        exit(1)

    print("Building mesh created.")
    print("Number of vertices:", building_mesh.vertices.shape[0])
    print("Number of faces:", building_mesh.faces.shape[0])

    output_path = os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
        "one_building_from_gml.obj",
    )
    try:
        building_mesh.export(output_path)
        print(f"Building mesh exported to {output_path}")
    except Exception as e:
        print("Failed to export building mesh:", e)

    try:
        building_mesh.show()
    except Exception as e:
        print("Interactive viewer failed:", e)
