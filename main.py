import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from rich.pretty import pprint
from project_paths import paths
import json
from pathlib import Path
from geopandas import GeoDataFrame
from shapely.geometry import Polygon

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


def make_request():
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
    node["highways"](area.bristol);
    way["highways"](area.bristol);
);
out;
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


def main():
    lsoa_files = find_lsoas()
    lsoa_polys = [get_polygons(Path(lsoa_file)) for lsoa_file in lsoa_files]
    lsoa_gdf = GeoDataFrame({"lsoa_code": lsoa_files, "geometry": lsoa_polys})

    print(lsoa_gdf)

    # data = make_request()
    # pprint(data)


if __name__ == "__main__":
    main()
