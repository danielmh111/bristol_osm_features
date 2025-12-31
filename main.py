import requests

overpass_url = "https://overpass-api.de/api/interpreter"

test_query_1 = """
[out:json][date:"2019-01-01T00:00:00Z"];
(
    node["amenity"](51.4,-2.7,51.5,-2.5);
    way["amenity"](51.4,-2.7,51.5,-2.5);
);
out center;
"""


test_query_2 = """
[out:json];
area["name"="Bristol"]["admin_level"="6"]->.bristol;
(
    node["amenity"="restaurant"](area.bristol);
    node["amenity"="cafe"](area.bristol);
    node["amenity"="pub"](area.bristol);
    way["amenity"="restaurant"](area.bristol);
    way["amenity"="cafe"](area.bristol);
    way["amenity"="pub"](area.bristol);
);
out center;
"""


test_query_3 = """
[out:json];
area["name"="Bristol"]["admin_level"="6"]->.bristol;
(
    node["amenity"="restaurant"](area.bristol);
    node["amenity"="cafe"](area.bristol);
    node["amenity"="pub"](area.bristol);
    way["amenity"="restaurant"](area.bristol);
    way["amenity"="cafe"](area.bristol);
    way["amenity"="pub"](area.bristol);
);
"""

test_query_4 = """
[out:json];
area["ISO3166-2"="GB-BST"]->.bristol;
(
    node["amenity"](area.bristol);
    way["amenity"](area.bristol);
);
out;
"""


def main():
    response = requests.get(
        overpass_url, 
        params={'data': test_query_4}
    )
    print(response.status_code)
    print(response.text)
    # print(response.json())


if __name__ == "__main__":
    main()
