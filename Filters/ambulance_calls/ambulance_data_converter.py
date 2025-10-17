import pandas as pd
import json
from shapely import wkt
from shapely.geometry import mapping, Polygon, MultiPolygon, box
from shapely.ops import unary_union
from pyproj import Transformer

# === FILES ===
csv_file = "spatiotemporal_grid_time_step=4.csv"
output_file = "amsterdam_grid_wgs84_fine.geojson"

# === TRANSFORMER: RD → WGS84 ===
transformer = Transformer.from_crs(28992, 4326, always_xy=True)

# Amsterdam bounding box in RD coordinates (adjusted for actual city center)
ams_bbox = (118000, 480000, 130000, 495000)  # Tighter around Amsterdam proper

def in_amsterdam(geom):
    """Check if geometry centroid is within Amsterdam bbox"""
    x, y = geom.centroid.coords[0]
    return ams_bbox[0] <= x <= ams_bbox[2] and ams_bbox[1] <= y <= ams_bbox[3]

def subdivide_polygon(poly, nx=2, ny=2):
    """
    Subdivide a polygon into nx * ny smaller grid cells.
    Returns list of smaller polygons.
    """
    minx, miny, maxx, maxy = poly.bounds
    width = (maxx - minx) / nx
    height = (maxy - miny) / ny
    
    subpolys = []
    for i in range(nx):
        for j in range(ny):
            x0 = minx + i * width
            y0 = miny + j * height
            x1 = x0 + width
            y1 = y0 + height
            subpoly = box(x0, y0, x1, y1)
            # Only include if it intersects with original polygon
            if poly.intersects(subpoly):
                subpolys.append(poly.intersection(subpoly))
    
    return subpolys

# === READ CSV ===
df = pd.read_csv(csv_file)

# Handle missing or invalid totals
df["Total"] = pd.to_numeric(df["Total"], errors="coerce").fillna(0)

# Calculate rate per 1000 residents (where population > 0)
df["rate_per_1000"] = 0.0
mask = df["aantal_inwoners"] > 0
df.loc[mask, "rate_per_1000"] = (df.loc[mask, "Total"] / df.loc[mask, "aantal_inwoners"]) * 1000

print(f"📊 Total column range: {df['Total'].min():.4f} to {df['Total'].max():.4f}")
print(f"📊 Rate per 1000 range: {df['rate_per_1000'].min():.4f} to {df['rate_per_1000'].max():.4f}")

amsterdam_features = []
subdivide_factor = 4  # Divide each 1000m cell into 4x4 = 16 smaller cells (250m each)

for _, row in df.iterrows():
    geom = wkt.loads(row["geometry"])
    if not in_amsterdam(geom):
        continue

    # Subdivide the geometry
    if isinstance(geom, Polygon):
        subpolys = subdivide_polygon(geom, subdivide_factor, subdivide_factor)
    elif isinstance(geom, MultiPolygon):
        subpolys = []
        for poly in geom.geoms:
            subpolys.extend(subdivide_polygon(poly, subdivide_factor, subdivide_factor))
    else:
        continue

    # Each subdivided cell gets the same properties
    for subpoly in subpolys:
        if not isinstance(subpoly, Polygon):
            continue
            
        # Transform to WGS84
        transformed = Polygon([
            transformer.transform(x, y) for x, y in subpoly.exterior.coords
        ])

        # === PROPERTIES ===
        props = {
            "c28992r1000": row["c28992r1000"],
            "population": int(row["aantal_inwoners"]) if pd.notna(row["aantal_inwoners"]) else 0,
            "total_calls": float(row["Total"]),
            "rate_per_1000": float(row["rate_per_1000"]),
            # Include time periods for potential future use
            "calls_0_4": float(row["0-4"]) if "0-4" in row else 0,
            "calls_4_8": float(row["4-8"]) if "4-8" in row else 0,
            "calls_8_12": float(row["8-12"]) if "8-12" in row else 0,
            "calls_12_16": float(row["12-16"]) if "12-16" in row else 0,
            "calls_16_20": float(row["16-20"]) if "16-20" in row else 0,
            "calls_20_0": float(row["20-0"]) if "20-0" in row else 0,
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

print(f"✅ Saved {len(amsterdam_features)} Amsterdam grid cells to {output_file}")
print(f"🔹 Original cells: ~{len(amsterdam_features) // (subdivide_factor ** 2)}")
print(f"🔹 Subdivision: {subdivide_factor}x{subdivide_factor} = {subdivide_factor**2} cells per original")
print(f"🔹 Cell size: ~{1000/subdivide_factor}m x {1000/subdivide_factor}m")