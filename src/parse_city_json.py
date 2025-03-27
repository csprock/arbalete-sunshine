from typing import List, Dict, Tuple, Any, Union
from cjio import cityjson
import cjio
import json
import pandas as pd
from pyproj import Transformer
import pvlib as pv
from src import get_logger
from src.config import SOURCE_EPSG, TARGET_EPSG
from src.geometry import shadow_bearing, shadow_length, translate_point, _get_intersection
from src.solar import get_time_series

transformer = Transformer.from_crs(SOURCE_EPSG, TARGET_EPSG)

LOGGER = get_logger(__name__, is_root=False)

def remove_empty_geometries(raw_json: dict) -> dict:

    ids_to_remove = []
    for _id, data in raw_json['CityObjects'].items():
        if 'geometry' not in data:
           ids_to_remove.append(_id) 
            
    for _id in ids_to_remove:
        LOGGER.debug(f"Removing {_id} from the CityJSON file")
        del raw_json['CityObjects'][_id]

    return raw_json


def preprocess_json(input_path: str, output_path: str) -> None:

    LOGGER.debug(f"Preprocessing CityJSON file {input_path} and saving it to {output_path}")
    with open(input_path, 'r') as f:
        raw_json = json.load(f)

    raw_json = remove_empty_geometries(raw_json)

    with open(output_path, 'w') as f:
        json.dump(raw_json, f)


def remove_empty_egid(co_dict: Dict[str, cjio.models.CityObject]) -> Dict[str, cjio.models.CityObject]:

    LOGGER.debug(f"Removing CityObjects without EGID")

    ids_to_remove = []
    for _id, data in co_dict.items():
        if 'EGID' not in data.attributes:
           ids_to_remove.append(_id) 
            
    for _id in ids_to_remove:
        LOGGER.debug(f"Removing {_id} from the CityJSON file")
        del co_dict[_id]

    return co_dict


def get_vertices(co: cjio.models.CityObject) -> List[Tuple[float, float, float]]:
    return co.get_vertices()

def get_minimum_height(vertex_list):
    min_height = 1e9

    for v in vertex_list:
        if v[2] < min_height:
            min_height = v[2]
    return min_height

def get_egid(co: cjio.models.CityObject) -> int:
    return co.attributes['EGID']

def process_single_building(co: cjio.models.CityObject) -> pd.DataFrame:

    egid = get_egid(co)
    vertices = get_vertices(co)
    vertices_df = pd.DataFrame(vertices, columns=['lat', 'long', 'z'])
    min_height = vertices_df['z'].min()
    altitude = min_height
    vertices_df['h'] = vertices_df['z'] - min_height
    vertices_df['altitude'] = altitude
    vertices_df['egid'] = egid

    return vertices_df

def process_boundary_generator(generator: iter, transformer: Transformer):
    return [x for x in transformer.itransform(generator)]
    

def convert_vertices_to_df(id: str, co: cjio.models.CityObject, transformer: Union[Transformer, None] = transformer) -> pd.DataFrame:

    vertex_list = co.get_vertices()
    if transformer is not None:
        vertex_list = process_boundary_generator(vertex_list, transformer)

    df = pd.DataFrame(vertex_list, columns = ['lat', 'lon', 'z'])
    df['egid'] = id

    return df




def process_multiple_buildings(co_dict: Dict[str, cjio.models.CityObject]) -> pd.DataFrame:

    dfs = pd.concat([convert_vertices_to_df(_id, x) for _id, x in co_dict.items()], ignore_index=True)

    # get the minumum z value for each egid
    min_heights = dfs.groupby('egid')['z'].min().reset_index()
    min_heights.columns = ['egid', 'min_height']
    dfs = dfs.merge(min_heights, on='egid')
    dfs['h'] = dfs['z'] - dfs['min_height']
    dfs['altitude'] = dfs['min_height']

    return dfs


def solar_position(df: pd.DataFrame, times: Union[pd.Timestamp, pd.DatetimeIndex]) -> pd.DataFrame:

    # get the solar position of each row in the df using the .apply function


    dfs = []

    for idx, row in df.iterrows():

        lat = row['lat']
        lon = row['lon']
        altitude = row['altitude']
        egid = row['egid']
        h = row['h']

        solar_position = pv.solarposition.get_solarposition(times, lat, lon, altitude=altitude).reset_index(names="time")

        solar_position['egid'] = egid
        solar_position['lat'] = lat
        solar_position['lon'] = lon
        solar_position['h'] = h
        
        dfs.append(solar_position)
    
    df = pd.concat(dfs, ignore_index=True)
    
    return df.loc[:, ['time', 'egid', 'lat', 'lon', 'elevation', 'azimuth','h']].copy()


def shadow_data_df(df: pd.DataFrame):

    df['shadow_bearing'] = shadow_bearing(df['azimuth'])
    df['shadow_length'] = shadow_length(df['elevation'], df['h'])

    return df


def translate_points_df(df: pd.DataFrame) -> pd.DataFrame:

    df['shadow_lat'], df['shadow_lon'] = translate_point(df['lat'].values, df['lon'].values, df['shadow_length'].values, df['shadow_bearing'].values)

    return df


def get_interesection_ratios(shadow_df: pd.DataFrame, terrace_df: pd.DataFrame) -> pd.DataFrame:

    results_tuple = []

    for idx, sub_df in shadow_df.groupby(['time', 'egid']):
        shadow = sub_df[['shadow_lat', 'shadow_lon']].values
        terrace = terrace_df[terrace_df['egid'] == idx[1]][['lat', 'lon']].values
        results_tuple.append((idx[0], idx[1], _get_intersection(shadow, terrace)[1]))

    results_df = pd.DataFrame(results_tuple, columns=['time', 'egid', 'intersection_ratio'])
    return results_df