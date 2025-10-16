import json
import pandas as pd
from pyproj import Transformer
from shapely.geometry import shape, mapping, Polygon, MultiPolygon

# Files
csv_file = "scaled_spatio_temporal_grid_time_step=4.csv"
geom_file = "1000x1000.json"
output_file = "amsterdam_grid_wgs84.geojson"

# Transformer RD -> WGS84
transformer = Transformer.from_crs(28992, 4326, always_xy=True)

# Amsterdam bounding box in RD
ams_bbox = (121000, 487000, 139000, 504000)

def in_amsterdam(geom):
    x, y = geom.centroid.coords[0]
    return ams_bbox[0] <= x <= ams_bbox[2] and ams_bbox[1] <= y <= ams_bbox[3]

# Read CSV
df = pd.read_csv(csv_file)
df.set_index('c28992r1000', inplace=True)  # use grid ID as index

# Load geometries
with open(geom_file, "r") as f:
    geo_data = json.load(f)

amsterdam_features = []
for feature in geo_data['features']:
    geom = shape(feature['geometry'])
    if not in_amsterdam(geom):
        continue  # skip non-Amsterdam cells

    grid_id = feature['properties'].get('c28992r1000')
    if grid_id not in df.index:
        continue  # skip if CSV has no data for this grid cell

    # Merge CSV properties
    props = df.loc[grid_id].to_dict()
    props['c28992r1000'] = grid_id

    # Transform geometry
    if isinstance(geom, Polygon):
        transformed = Polygon([transformer.transform(x, y) for x, y in geom.exterior.coords])
    elif isinstance(geom, MultiPolygon):
        transformed = MultiPolygon([
            Polygon([transformer.transform(x, y) for x, y in poly.exterior.coords])
            for poly in geom.geoms
        ])
    else:
        continue

    amsterdam_features.append({
        "type": "Feature",
        "properties": props,
        "geometry": mapping(transformed)
    })

geojson = {"type": "FeatureCollection", "features": amsterdam_features}

with open(output_file, "w") as f:
    json.dump(geojson, f, indent=2)

print(f"Saved {len(amsterdam_features)} Amsterdam features to {output_file}")