import json
from pyproj import Transformer
from shapely.geometry import shape, mapping, Polygon, MultiPolygon

# File paths
input_file = "1000x1000.json"
output_file = "amsterdam_grid_wgs84.geojson"

# RD -> WGS84 transformer
transformer = Transformer.from_crs(28992, 4326, always_xy=True)

# Load JSON
with open(input_file, "r") as f:
    data = json.load(f)

# Filter Amsterdam features
amsterdam_features = [
    feature for feature in data['features']
    if feature['properties'].get('city') == 'Amsterdam'
]

# Convert geometry to WGS84
for feature in amsterdam_features:
    geom = shape(feature['geometry'])
    # Transform all coordinates
    if isinstance(geom, Polygon):
        transformed = Polygon([transformer.transform(x, y) for x, y in geom.exterior.coords])
    elif isinstance(geom, MultiPolygon):
        transformed = MultiPolygon([
            Polygon([transformer.transform(x, y) for x, y in poly.exterior.coords])
            for poly in geom.geoms
        ])
    else:
        raise ValueError(f"Unsupported geometry type: {type(geom)}")
    feature['geometry'] = mapping(transformed)

# Optionally filter out zero-density cells
amsterdam_features = [
    f for f in amsterdam_features
    if f['properties'].get('omgevingsadressendichtheid', 0) > 0
]

# Save to GeoJSON
geojson = {
    "type": "FeatureCollection",
    "features": amsterdam_features
}

with open(output_file, "w") as f:
    json.dump(geojson, f)

print(f"Saved {len(amsterdam_features)} Amsterdam features to {output_file}")