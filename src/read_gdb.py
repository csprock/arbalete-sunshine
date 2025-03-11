"""
Module to load one building and its matching roof from the File Geodatabase, by matching
via spatial intersection of 2D footprints.

This example uses the "Building_solid" layer to load one building and the "Roof_solid"
layer to search for a roof whose 2D footprint intersects the building's footprint. The
building is extruded using its computed height. For the roof, we re-extrude its 2D
footprint to a fixed thickness (0.2 m) and then align it vertically with the building
(i.e. translating the roof so that its bottom equals the building’s top). The combined
result can then be exported or further processed.
"""

import os
import fiona
from shapely.geometry import shape, Polygon
from shapely.ops import unary_union
import trimesh

# Default parameters
DEFAULT_BUILDING_HEIGHT = 10.0
DEFAULT_ROOF_THICKNESS = 0.2


def extract_footprint_and_height(poly: Polygon, default_height=10.0):
    """
    Given a 3D Polygon, extract the 2D footprint (projecting x,y from the exterior) and
    compute the height.
    """
    coords = list(poly.exterior.coords)
    if len(coords[0]) < 3:
        return poly, default_height
    xs = [pt[0] for pt in coords]
    ys = [pt[1] for pt in coords]
    zs = [pt[2] for pt in coords]
    footprint = Polygon(zip(xs, ys))
    h = max(zs) - min(zs)
    if h == 0:
        h = default_height
    return footprint, h


def process_geometry(geom):
    """
    Given a shapely geometry, return a valid Polygon.
    If the geometry is a MultiPolygon, union its parts.
    If the union yields a GeometryCollection, extract and return the largest Polygon.
    """
    if geom.is_empty:
        return None
    if geom.geom_type == "Polygon":
        return geom
    elif geom.geom_type == "MultiPolygon":
        unioned = unary_union(geom.geoms)
        if unioned.is_empty:
            return None
        if unioned.geom_type == "Polygon":
            return unioned
        elif unioned.geom_type == "GeometryCollection":
            polys = [g for g in unioned if g.geom_type == "Polygon"]
            if polys:
                return max(polys, key=lambda p: p.area)
    return None


def extrude_feature_geometry(feature, default_height=10.0):
    """
    Convert a Fiona feature into a 3D mesh.
    Returns (mesh, height, footprint)
    """
    geom = shape(feature["geometry"])
    poly = None
    if geom.geom_type in ["Polygon", "MultiPolygon"]:
        poly = process_geometry(geom)
    else:
        raise ValueError("Unsupported geometry type: " + str(geom.geom_type))
    if poly is None:
        raise ValueError("Could not extract a valid Polygon.")
    footprint, h = extract_footprint_and_height(poly, default_height=default_height)
    try:
        mesh = trimesh.creation.extrude_polygon(footprint, height=h)
    except Exception as e:
        raise RuntimeError(f"Extrusion failed: {e}")
    return mesh, h, footprint


def load_first_feature(gdb_path: str, layer: str, default_height=10.0):
    """
    Load the first feature from a given layer.
    Returns (mesh, height, footprint, properties)
    """
    with fiona.open(gdb_path, layer=layer) as src:
        feature = next(iter(src), None)
        if feature is None:
            raise ValueError(f"No features found in layer {layer}.")
        mesh, h, footprint = extrude_feature_geometry(feature, default_height)
        return mesh, h, footprint, feature["properties"]


def load_all_features(gdb_path: str, layer: str, default_height=10.0):
    """
    Load all features from a given layer and return a list of tuples:
      (mesh, height, footprint, properties)
    """
    features = []
    with fiona.open(gdb_path, layer=layer) as src:
        for feature in src:
            try:
                mesh, h, footprint = extrude_feature_geometry(feature, default_height)
                features.append((mesh, h, footprint, feature["properties"]))
            except Exception as e:
                # Skip features that cannot be processed.
                print(f"Skipping feature due to error: {e}")
    return features


def find_matching_roof(building_footprint, roof_features):
    """
    Given a building 2D footprint (a Shapely Polygon) and a list of roof features (each
    a tuple of (mesh, height, footprint, properties)), find the roof whose footprint has
    the largest intersection area with the building footprint.

    Returns the matching roof feature tuple, or None if none intersect.
    """
    best_roof = None
    best_area = 0.0
    for roof in roof_features:
        _, _, roof_fp, _ = roof
        inter = building_footprint.intersection(roof_fp)
        if not inter.is_empty:
            area = inter.area
            if area > best_area:
                best_area = area
                best_roof = roof
    return best_roof


if __name__ == "__main__":
    # Construct path to the GDB.
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    gdb_path = os.path.join(base_dir, "data", "swissBUILDINGS3D_3-0_1301-13.gdb")

    # For this example, use the "Building_solid" and "Roof_solid" layers.
    print("Loading one building from 'Building_solid' layer...")
    try:
        building_mesh, b_height, building_fp, b_props = load_first_feature(
            gdb_path, layer="Building_solid", default_height=DEFAULT_BUILDING_HEIGHT
        )
    except Exception as e:
        print(f"Error loading building: {e}")
        exit(1)

    print("Building loaded.")
    print("Building properties:")
    for k, v in b_props.items():
        print(f"  {k}: {v}")

    # Load all roof features.
    print("Loading roof features from 'Roof_solid' layer...")
    roof_features = load_all_features(
        gdb_path, layer="Roof_solid", default_height=DEFAULT_ROOF_THICKNESS
    )
    print(f"Loaded {len(roof_features)} roof features.")

    # Find a roof that best matches the building footprint.
    matching_roof = find_matching_roof(building_fp, roof_features)
    if matching_roof is None:
        print("No matching roof found for the building.")
        combined_mesh = building_mesh
    else:
        roof_mesh, r_height, roof_fp, r_props = matching_roof
        print("Found matching roof feature.")
        # Re-extrude the roof footprint to a fixed thickness (DEFAULT_ROOF_THICKNESS).
        try:
            roof_mesh_fixed = trimesh.creation.extrude_polygon(
                roof_fp, height=DEFAULT_ROOF_THICKNESS
            )
        except Exception as e:
            print(f"Roof re-extrusion failed: {e}")
            roof_mesh_fixed = roof_mesh
        # Align the roof: translate so that its bottom aligns with the building's top.
        building_top = building_mesh.bounds[1, 2]
        roof_bottom = roof_mesh_fixed.bounds[0, 2]
        translation_z = building_top - roof_bottom
        roof_mesh_fixed.apply_translation([0, 0, translation_z])
        # Combine the building and roof meshes.
        combined_mesh = trimesh.util.concatenate([building_mesh, roof_mesh_fixed])

    # For debugging, print combined mesh stats.
    print("Combined mesh bounding box:", combined_mesh.bounds)
    print("Number of vertices:", combined_mesh.vertices.shape[0])
    print("Number of faces:", combined_mesh.faces.shape[0])

    # Option: export the combined mesh to an OBJ file.
    output_path = os.path.join(base_dir, "one_building_with_roof.obj")
    try:
        combined_mesh.export(output_path)
        print(f"Combined mesh exported to {output_path}")
    except Exception as e:
        print(f"Failed to export combined mesh: {e}")
