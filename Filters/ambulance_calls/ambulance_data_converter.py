import json
from pyproj import Transformer
from shapely.geometry import shape, mapping, Polygon, MultiPolygon

# Input/output
input_file = "scaled_spatio_temporal_grid_time_step=4.json"  # your original JSON
output_file = "amsterdam_grid_wgs84.geojson"

# Transformer RD -> WGS84
transformer = Transformer.from_crs(28992, 4326, always_xy=True)

# Approximate Amsterdam bounding box in EPSG:28992 (xmin, ymin, xmax, ymax)
ams_bbox = (121000, 487000, 139000, 504000)

def in_amsterdam(geom):
    """Check if geometry centroid is within Amsterdam bounding box"""
    x, y = geom.centroid.coords[0]
    return (ams_bbox[0] <= x <= ams_bbox[2]) and (ams_bbox[1] <= y <= ams_bbox[3])

# Load JSON
with open(input_file, "r") as f:
    data = json.load(f)

# Filter and transform
amsterdam_features = []
for feature in data['features']:
    geom = shape(feature['geometry'])
    if not in_amsterdam(geom):
        continue  # skip features outside Amsterdam

    # Keep relevant properties
    props = {
        "c28992r1000": feature['properties'].get('c28992r1000'),
        "0-4": feature['properties'].get('0-4'),
        "4-8": feature['properties'].get('4-8'),
        "8-12": feature['properties'].get('8-12'),
        "12-16": feature['properties'].get('12-16'),
        "16-20": feature['properties'].get('16-20'),
        "20-0": feature['properties'].get('20-0'),
        "Total": feature['properties'].get('Total')
    }

    # Transform geometry
    if isinstance(geom, Polygon):
        transformed = Polygon([transformer.transform(x, y) for x, y in geom.exterior.coords])
    elif isinstance(geom, MultiPolygon):
        transformed = MultiPolygon([
            Polygon([transformer.transform(x, y) for x, y in poly.exterior.coords])
            for poly in geom.geoms
        ])
    else:
        continue  # skip unknown geometry types

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