from cjio import cityjson
import cjio
from pandas import Timestamp
import datetime


from src import get_logger
from src.parse_city_json import remove_empty_egid
from src.parse_city_json import process_multiple_buildings
from src.parse_city_json import solar_position
from src.parse_city_json import shadow_data_df
from src.parse_city_json import translate_points_df
from src.geometry import get_convex_hulls
from src.solar import get_time_series


LOGGER = get_logger(__name__, is_root=True)

if __name__ == "__main__":
    # remove empty ID

    LOGGER.info("Loading CityJSON file")
    cm = cityjson.load("/app/data/swissBUILDINGS3D_3-0_1047-43.json", transform=True)
    LOGGER.info("Removing empty CityObjects")
    buildings = remove_empty_egid(cm.get_cityobjects(type="building"))
    

    LOGGER.info(f"Number of buildings: {len(buildings)}")
    LOGGER.info("Getting list of EGID")
    # get list of EGID and sample 5 of them
    egid_list = [co.attributes["EGID"] for co in buildings.values()]

    # take a random sample of egid_list
    import random
    random.seed(42)
    sample_egid = random.sample(egid_list, 5)
    LOGGER.info(f"Sample of EGID: {sample_egid}")

    # filter buildings by EGID in egid_list
    LOGGER.info("Filtering buildings by EGID")
    buildings_filtered = {k: v for k, v in buildings.items() if v.attributes["EGID"] in sample_egid}
    LOGGER.info(f"Number of buildings after filtering: {len(buildings_filtered)}")


    buildings_df = process_multiple_buildings(buildings_filtered)

    times = get_time_series('2023-06-21', freq='1h')

    building_points_with_solar = solar_position(buildings_df, times)
    building_points_with_solar = shadow_data_df(building_points_with_solar)



    # count the fraction of NaN values in the elevation, azimuth, shadow_bearing and shadow_length columns
    LOGGER.info("Fraction of NaN values in the elevation, azimuth, shadow_bearing and shadow_length columns")

    LOGGER.info(f"Elevation: {building_points_with_solar['elevation'].isna().sum() / len(building_points_with_solar)}")
    LOGGER.info(f"Azimuth: {building_points_with_solar['azimuth'].isna().sum() / len(building_points_with_solar)}")
    LOGGER.info(f"Shadow_bearing: {building_points_with_solar['shadow_bearing'].isna().sum() / len(building_points_with_solar)}")
    LOGGER.info(f"Shadow_length: {building_points_with_solar['shadow_length'].isna().sum() / len(building_points_with_solar)}")


    print(building_points_with_solar.head())
    building_points_with_solar.to_csv("/app/data/building_points_with_solar.csv", index=False)


    translated_points_df = translate_points_df(building_points_with_solar)
    translated_points_df.to_csv("/app/data/translated_points.csv", index=False)
    LOGGER.info("Data saved to /app/data/building_points_with_solar.csv and /app/data/translated_points.csv")

    

    convex_hulls_df = get_convex_hulls(translated_points_df)
    convex_hulls_df.to_csv("/app/data/convex_hulls.csv", index=False)
    LOGGER.info("Data saved to /app/data/convex_hulls.csv")