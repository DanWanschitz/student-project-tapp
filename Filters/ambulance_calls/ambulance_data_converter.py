import pandas as pd
import json
from shapely import wkt
from shapely.geometry import mapping, Polygon, MultiPolygon
from pyproj import Transformer

# === FILES ===
csv_file = "spatiotemporal_grid_time_step=4.csv"  # unscaled data
output_file = "amsterdam_grid_wgs84_scaled.geojson"

# === TRANSFORMER: RD → WGS84 ===
transformer = Transformer.from_crs(28992, 4326, always_xy=True)

# Amsterdam bounding box in RD coordinates
ams_bbox = (121000, 487000, 139000, 504000)

def in_amsterdam(geom):
    x, y = geom.centroid.coords[0]
    return ams_bbox[0] <= x <= ams_bbox[2] and ams_bbox[1] <= y <= ams_bbox[3]

# === READ CSV ===
df = pd.read_csv(csv_file)

# Handle missing or invalid totals
df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)

# === SCALE TOTAL COLUMN 0–1 ===
min_val, max_val = df["Total"].min(), df["Total"].max()
if max_val != min_val:
    df["Total_scaled"] = (df["Total"] - min_val) / (max_val - min_val)
else:
    df["Total_scaled"] = 0  # fallback if all totals are identical

amsterdam_features = []
for _, row in df.iterrows():
    geom = wkt.loads(row["geometry"])
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

    # === PROPERTIES ===
    props = {
        "c28992r1000": row["c28992r1000"],
        "Total": row["Total"],
        "Total_scaled": row["Total_scaled"]
    }

    amsterdam_features.append({
        "type": "Feature",
        "properties": props,
        "geometry": mapping(transformed)
    })

# === SAVE GEOJSON ===
geojson = {"type": "FeatureCollection", "features": amsterdam_features}

with open(output_file, "w") as f:
    json.dump(geojson, f, indent=2)

print(f"✅ Saved {len(amsterdam_features)} Amsterdam features to {output_file}")
print(f"🔹 Range scaled: {min_val:.4f} → {max_val:.4f}")
