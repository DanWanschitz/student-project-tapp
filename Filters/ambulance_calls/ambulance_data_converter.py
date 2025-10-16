import pandas as pd
import json
from shapely import wkt
from shapely.geometry import mapping, Polygon, MultiPolygon
from pyproj import Transformer

# Files
csv_file = "spatiotemporal_grid_time_step=4.csv"  # your CSV
output_file = "amsterdam_grid_wgs84.geojson"

# Transformer RD -> WGS84
transformer = Transformer.from_crs(28992, 4326, always_xy=True)

# Amsterdam bounding box in RD coordinates
ams_bbox = (121000, 487000, 139000, 504000)

def in_amsterdam(geom):
    x, y = geom.centroid.coords[0]
    return ams_bbox[0] <= x <= ams_bbox[2] and ams_bbox[1] <= y <= ams_bbox[3]

# Read CSV
df = pd.read_csv(csv_file)

amsterdam_features = []
for _, row in df.iterrows():
    geom = wkt.loads(row['geometry'])
    if not in_amsterdam(geom):
        continue

    # Transform geometry to WGS84
    if isinstance(geom, Polygon):
        transformed = Polygon([transformer.transform(x, y) for x, y in geom.exterior.coords])
    elif isinstance(geom, MultiPolygon):
        transformed = MultiPolygon([
            Polygon([transformer.transform(x, y) for x, y in poly.exterior.coords])
            for poly in geom.geoms
        ])
    else:
        continue

    props = {
        "c28992r1000": row['c28992r1000'],
        "0-4": row['0-4'],
        "4-8": row['4-8'],
        "8-12": row['8-12'],
        "12-16": row['12-16'],
        "16-20": row['16-20'],
        "20-0": row['20-0'],
        "Total": row['Total']
    }

    amsterdam_features.append({
        "type": "Feature",
        "properties": props,
        "geometry": mapping(transformed)
    })

geojson = {"type": "FeatureCollection", "features": amsterdam_features}

with open(output_file, "w") as f:
    json.dump(geojson, f, indent=2)

print(f"Saved {len(amsterdam_features)} Amsterdam features to {output_file}")