import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from rich.pretty import pprint
from project_paths import paths
import json
from pathlib import Path
from geopandas import GeoDataFrame
from shapely.geometry import Polygon
from functools import cache
from collections import Counter
from itertools import chain

LOCATIONS = paths.locations
DATA = paths.data


def find_lsoas() -> list[str]:
    files = LOCATIONS.iterdir()
    names = [file.parts[-1].removesuffix(".geojson") for file in files]
    return names


def get_polygons(polygon_file: Path) -> Polygon:
    with open(LOCATIONS / f"{polygon_file}.geojson") as file:
        polygon = json.load(file)

    coords = polygon["coordinates"][0]

    geometry = Polygon(coords)
    return geometry


@cache
def fetch_bristol_data():
    overpass_url = "https://overpass-api.de/api/interpreter"
    bristol_data_query = """
[out:json];
area["ISO3166-2"="GB-BST"]->.bristol;
(
    node["amenity"](area.bristol);
    way["amenity"](area.bristol);
    node["shop"](area.bristol);
    way["shop"](area.bristol);
    node["landuse"](area.bristol);
    way["landuse"](area.bristol);
    node["highway"](area.bristol);
    way["highway"](area.bristol);
);
out geom;
"""

    retry_logic = Retry(
        total=5,
        status_forcelist=[429, 500, 503, 504],
        backoff_factor=1,
        respect_retry_after_header=True,
    )

    with requests.Session() as session:
        session.mount("https://", HTTPAdapter(max_retries=retry_logic))
        response = session.get(overpass_url, params={"data": bristol_data_query})

    response.raise_for_status()

    return response.json()


# count of ammenities


# distance to nearest...


# ratio of ... to ...


# road layout


# landuses


# streetlighting


# total points of interest


# variaty of points of interest


# for anything counting items, we want to define buffers of different distances
# e.g. 250 meters, 500 meters, 1km, 5km
# could be done to represent walking distance, short trip away, long trip away.

# i wont try and guess the most appropriate distance for each feature yet, will produce lots of different ones and come onto feature selection and dimensionality reduction through some experiments later

# also, for lots of these there will be some variation in what counts. e.g. count of ammenities can be broken down into retail, hospitality etc.
# these could be weighted or different features could be produced for each category

# this means that there will be lots of combinations of the different variations on each feature, possibly leading to over 500 differnt features
# in some cases the different variants could be produced by the same function with different parameters e.g. distance buffer could be an argument
# but im keen to make sure i dont write hundreds of functions that will be impossible to read through - factory pattern possible?

# basically, for each feature type we want there to be one computation (code) and lots of parameters (data). This way, we could write a small number of flexible functions, then write out a config object.
# ill start by just writing some pure functions for extracting examples of the features to be extracted


def main():
    lsoa_files = find_lsoas()
    lsoa_polys = [get_polygons(Path(lsoa_file)) for lsoa_file in lsoa_files]
    lsoa_gdf = GeoDataFrame({"lsoa_code": lsoa_files, "geometry": lsoa_polys})
    lsoa_gdf = lsoa_gdf.set_crs(epsg=4326)  # coords start in lat/long degrees
    lsoa_gdf = lsoa_gdf.to_crs(epsg=27700)  # convert to metric coords
    lsoa_gdf = lsoa_gdf.assign(
        **{
            f"geom_{distance}": lsoa_gdf.geometry.buffer(distance)
            for distance in [0, 250, 500, 750, 1000, 1250, 1500, 2000, 2500, 5000]
        }
    )  # create geometries of lsoas extended by different distances in meters

    print(lsoa_gdf)

    lsoa_gdf.to_csv("test.csv")

    # data = fetch_bristol_data()
    # map_elements = data["elements"]

    # point_data = [element for element in map_elements if element.get("type") == "node"]
    # polygon_data = [
    #     element
    #     for element in map_elements
    #     if element.get("type") == "way" and "highway" not in element.get("tags").keys()
    # ]
    # line_data = [
    #     element for element in map_elements if "highway" in element.get("tags").keys()
    # ]

    # print(len(point_data))
    # print(len(polygon_data))
    # print(len(line_data))


if __name__ == "__main__":
    main()
