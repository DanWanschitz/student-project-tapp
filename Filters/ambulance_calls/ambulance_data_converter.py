import json
from pyproj import Transformer
from shapely.geometry import shape, mapping, Polygon, MultiPolygon

# Input/output
input_file = "1000x1000.json"
output_file = "amsterdam_grid_wgs84.geojson"

# Transformer RD -> WGS84
transformer = Transformer.from_crs(28992, 4326, always_xy=True)

# Load JSON
with open(input_file, "r") as f:
    data = json.load(f)

# Filter Amsterdam and keep only relevant properties
amsterdam_features = []
for feature in data['features']:
    if feature['properties'].get('city') == 'Amsterdam':
        # Keep only properties you need
        props = {
            "omgevingsadressendichtheid": feature['properties'].get('omgevingsadressendichtheid'),
            "c28992r1000": feature['properties'].get('c28992r1000')
        }

        geom = shape(feature['geometry'])
        # Transform geometry
        if isinstance(geom, Polygon):
            transformed = Polygon([transformer.transform(x, y) for x, y in geom.exterior.coords])
        elif isinstance(geom, MultiPolygon):
            transformed = MultiPolygon([
                Polygon([transformer.transform(x, y) for x, y in poly.exterior.coords])
                for poly in geom.geoms
            ])
        else:
            continue  # skip unknown geometry

        amsterdam_features.append({
            "type": "Feature",
            "properties": props,
            "geometry": mapping(transformed)
        })

# Create FeatureCollection
geojson = {
    "type": "FeatureCollection",
    "features": amsterdam_features
}

# Save with pretty-print
with open(output_file, "w") as f:
    json.dump(geojson, f, indent=2)

print(f"Saved {len(amsterdam_features)} Amsterdam features to {output_file}")