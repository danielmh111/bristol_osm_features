import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from rich.pretty import pprint
from project_paths import paths
import json
from pathlib import Path
from geopandas import GeoDataFrame
from shapely.geometry import Polygon, Point, LineString
from collections import Counter
from itertools import chain
import pandas as pd

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


def count_ammenities(
    feature_frame: GeoDataFrame,
    point_osm_data: list,
    ammenities: list,
    distance: int,
) -> pd.Series: ...


def find_nearest_poi(
    feature_frame: GeoDataFrame,
    point_osm_data: list,
    poi: str,
    distance: int,
) -> pd.Series: ...


def calculate_ratio_of_elements(
    feature_frame: GeoDataFrame,
    point_osm_data: list,
    elements: tuple[str, str],
    distance: int,
) -> pd.Series: ...


def find_landuse_share(
    feature_frame: GeoDataFrame,
    polygon_osm_data: list,
    distance: int,
) -> pd.Series: ...


def find_streetlit_path_percent(
    feature_frame: GeoDataFrame,
    line_osm_data: list,
    distance: int,
) -> pd.Series: ...


def calculate_poi_diversity(
    feature_frame: GeoDataFrame,
    point_osm_data: list,
    distance: int,
) -> pd.Series: ...


def find_total_pois(
    feature_frame: GeoDataFrame,
    point_osm_data: list,
    distance: int,
) -> pd.Series: ...


def format_osm_geodataframes(
    map_elements: list,
) -> tuple[GeoDataFrame, GeoDataFrame, GeoDataFrame]:
    # seperate out map elements of different geometries

    point_data = [element for element in map_elements if element.get("type") == "node"]
    polygon_data = [
        element
        for element in map_elements
        if element.get("type") == "way"
        and "highway" not in element.get("tags", {}).keys()
        and len(element.get("geometry", [])) >= 4
    ]
    line_data = [
        element
        for element in map_elements
        if element.get("type") == "way" and "highway" in element.get("tags", {}).keys()
    ]

    invalid_polygons = [
        element
        for element in map_elements
        if element.get("type") == "way"
        and "highway" not in element.get("tags", {}).keys()
        and len(element.get("geometry", [])) < 4
    ]  # ? maybe have to convert these to nodes? they're all benches, probably fine to exclude

    # create a geodataframe for each geometry type.
    # specify the lon/lat degrees coord system when creating, then convert each to metric to match the lsoa dataframe format

    points_gdf = GeoDataFrame(
        data=point_data,
        geometry=[Point(element["lon"], element["lat"]) for element in point_data],
        crs="EPSG:4326",
    )
    points_gdf = points_gdf.to_crs(epsg=27700)

    polygons_gdf = GeoDataFrame(
        data=polygon_data,
        geometry=[
            Polygon(
                [
                    (node.get("lat"), node.get("lon"))
                    for node in element.get("geometry", {})
                ]
            )
            for element in polygon_data
        ],
        crs="EPSG:4326",
    )
    polygons_gdf = polygons_gdf.to_crs(epsg=27700)

    lines_gdf = GeoDataFrame(
        data=line_data,
        geometry=[
            LineString(
                [
                    (node.get("lat"), node.get("lon"))
                    for node in element.get("geometry", {})
                ]
            )
            for element in line_data
        ],
        crs="EPSG:4326",
    )
    lines_gdf = lines_gdf.to_crs(epsg=27700)

    return points_gdf, polygons_gdf, lines_gdf


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

    data = fetch_bristol_data()
    map_elements = data["elements"]

    osm_points_gdf, osm_polygons_gdf, osm_lines_gdf = format_osm_geodataframes(
        map_elements=map_elements
    )

    print(osm_points_gdf)
    print(osm_polygons_gdf)
    print(osm_lines_gdf)


if __name__ == "__main__":
    main()
