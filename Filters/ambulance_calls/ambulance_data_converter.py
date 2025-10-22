"""
Convert spatiotemporal grid CSV to GeoJSON grid polygons
Preserves the actual grid structure without jittering
Each polygon represents a grid cell with aggregated call data by hour

This maintains data accuracy by keeping the original grid structure
"""

import pandas as pd
import json
from shapely import wkt
from shapely.geometry import mapping
from pyproj import Transformer

# === CONFIGURATION ===
csv_file = "AMS_spatiotemporal_grid_time_step=1.csv"  # hourly data
output_file = "amsterdam_ambulance_grid.geojson"

# Transformer: RD → WGS84
transformer = Transformer.from_crs(28992, 4326, always_xy=True)

def transform_polygon(geom):
    """Transform polygon from RD to WGS84"""
    coords = geom.exterior.coords
    transformed_coords = [transformer.transform(x, y) for x, y in coords]
    return transformed_coords

print("=" * 70)
print("Converting Grid Data to GeoJSON Polygons")
print("=" * 70)
print()

# Read CSV
print("📂 Reading CSV file...")
df = pd.read_csv(csv_file)

# Hour columns
hour_cols = [f"{i}-{i+1}" for i in range(23)] + ["23-0"]

# Clean data
for col in hour_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

df["aantal_inwoners"] = pd.to_numeric(df["aantal_inwoners"], errors="coerce").fillna(0)

print(f"   ✅ Loaded {len(df)} grid cells")
print()

# Convert to GeoJSON features
print("📍 Converting grid cells to GeoJSON polygons...")
features = []

for idx, row in df.iterrows():
    if idx % 100 == 0:
        print(f"   Progress: {idx}/{len(df)} cells", end='\r')
    
    # Parse geometry
    try:
        geom = wkt.loads(row["geometry"])
    except:
        continue
    
    # Transform to WGS84
    transformed_coords = transform_polygon(geom)
    
    # Calculate total calls and by period
    calls_by_hour = {}
    total_calls = 0
    
    night_calls = 0      # 23, 0, 1, 2, 3, 4
    morning_calls = 0    # 5-10
    afternoon_calls = 0  # 11-16
    evening_calls = 0    # 17-22
    
    for hour_col in hour_cols:
        if hour_col not in row:
            continue
        
        calls = row[hour_col]
        if pd.isna(calls):
            calls = 0
        
        hour = int(hour_col.split('-')[0])
        calls_by_hour[hour] = float(calls)
        total_calls += calls
        
        # Aggregate by period
        if hour in [23, 0, 1, 2, 3, 4]:
            night_calls += calls
        elif 5 <= hour <= 10:
            morning_calls += calls
        elif 11 <= hour <= 16:
            afternoon_calls += calls
        else:
            evening_calls += calls
    
    # Skip empty cells
    if total_calls == 0:
        continue
    
    # Create feature
    feature = {
        'type': 'Feature',
        'geometry': {
            'type': 'Polygon',
            'coordinates': [transformed_coords]
        },
        'properties': {
            'grid_id': int(row['c28992r1000']),
            'population': int(row['aantal_inwoners']),
            'total_calls': float(total_calls),
            'night_calls': float(night_calls),
            'morning_calls': float(morning_calls),
            'afternoon_calls': float(afternoon_calls),
            'evening_calls': float(evening_calls),
            'calls_by_hour': calls_by_hour
        }
    }
    
    features.append(feature)

print(f"\n   ✅ Processed {len(features)} grid cells with ambulance calls")
print()

# Calculate statistics
total_calls_all = sum(f['properties']['total_calls'] for f in features)
period_totals = {
    'night': sum(f['properties']['night_calls'] for f in features),
    'morning': sum(f['properties']['morning_calls'] for f in features),
    'afternoon': sum(f['properties']['afternoon_calls'] for f in features),
    'evening': sum(f['properties']['evening_calls'] for f in features)
}

# Create GeoJSON
print("💾 Creating GeoJSON...")
geojson = {
    'type': 'FeatureCollection',
    'features': features,
    'metadata': {
        'source': csv_file,
        'total_grid_cells': len(features),
        'total_calls': float(total_calls_all),
        'calls_by_period': period_totals,
        'note': 'Grid polygons preserve original spatial accuracy'
    }
}

with open(output_file, 'w') as f:
    json.dump(geojson, f, indent=2)

print(f"✅ Saved to {output_file}")
print()
print("📊 Summary Statistics:")
print(f"   Total grid cells: {len(features):,}")
print(f"   Total calls: {total_calls_all:,.2f}")
print()
print("   By Time Period:")
for period, count in period_totals.items():
    pct = (count / total_calls_all * 100) if total_calls_all else 0
    print(f"      {period.capitalize():12s}: {count:8,.2f} ({pct:5.1f}%)")
print()
print("✅ Ready for grid visualization")