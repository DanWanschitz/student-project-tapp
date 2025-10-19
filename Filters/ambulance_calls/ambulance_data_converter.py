"""
Convert spatiotemporal grid CSV to point-based GeoJSON
Creates individual point features for each call based on grid cell centers and hourly counts

This simulates individual ambulance calls from aggregated grid data
"""

import pandas as pd
import json
from shapely import wkt
from shapely.geometry import Point, mapping
from pyproj import Transformer
import random
from datetime import datetime, timedelta

# === CONFIGURATION ===
csv_file = "AMS_spatiotemporal_grid_time_step=1.csv"  # hourly data
output_file = "amsterdam_ambulance_points_from_grid.geojson"

# Base date for the data (2017-2019 autumn seasons)
# We'll simulate dates across this range
START_DATE = datetime(2017, 9, 1)  # Sept 1, 2017
END_DATE = datetime(2019, 11, 30)  # Nov 30, 2019

# Transformer: RD → WGS84
transformer = Transformer.from_crs(28992, 4326, always_xy=True)

# Amsterdam bounding box in RD
AMS_BBOX = (118000, 480000, 130000, 495000)

def is_in_amsterdam(x, y):
    """Check if RD coordinates are in Amsterdam"""
    return AMS_BBOX[0] <= x <= AMS_BBOX[2] and AMS_BBOX[1] <= y <= AMS_BBOX[3]

def get_polygon_center(geom):
    """Get center point of polygon in RD coordinates"""
    centroid = geom.centroid
    return centroid.x, centroid.y

def jitter_point(x, y, cell_size=1000, jitter_fraction=0.4):
    """
    Add random jitter to avoid all points being at exact cell center
    jitter_fraction: how much of cell size to use for jitter (0.4 = ±40% of cell)
    """
    jitter_amount = cell_size * jitter_fraction
    x_jittered = x + random.uniform(-jitter_amount, jitter_amount)
    y_jittered = y + random.uniform(-jitter_amount, jitter_amount)
    return x_jittered, y_jittered

def generate_random_dates(num_calls, start_date, end_date):
    """
    Generate random dates within range
    For simplicity, spread evenly across the date range
    """
    date_range = (end_date - start_date).days
    dates = []
    for _ in range(num_calls):
        random_days = random.randint(0, date_range)
        date = start_date + timedelta(days=random_days)
        dates.append(date)
    return sorted(dates)

print("=" * 70)
print("Converting Grid Data to Point-Based GeoJSON")
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

# Convert to points
print("📍 Converting grid cells to individual call points...")
features = []
total_calls = 0
cells_processed = 0

for idx, row in df.iterrows():
    if idx % 100 == 0:
        print(f"   Progress: {idx}/{len(df)} cells", end='\r')
    
    # Parse geometry
    try:
        geom = wkt.loads(row["geometry"])
    except:
        continue
    
    # Get center in RD
    center_x, center_y = get_polygon_center(geom)
    
    # Check if in Amsterdam
    if not is_in_amsterdam(center_x, center_y):
        continue
    
    cells_processed += 1
    
    # Process each hour
    for hour_col in hour_cols:
        if hour_col not in row:
            continue
        
        call_count = row[hour_col]
        
        # Skip if no calls
        if call_count == 0 or pd.isna(call_count):
            continue
        
        # Determine hour from column name
        hour = int(hour_col.split('-')[0])
        
        # Determine time period
        if hour in [23, 0, 1, 2, 3, 4]:
            period = 'night'
        elif 5 <= hour < 11:
            period = 'morning'
        elif 11 <= hour < 17:
            period = 'afternoon'
        else:
            period = 'evening'
        
        # Since call_count is a decimal (rate/density), we need to interpret it
        # Option 1: Round to nearest integer (treat as approximate count)
        # Option 2: Use as-is and create fractional representation
        
        # We'll round and create that many points
        num_points = max(1, round(call_count * 100))  # Scale up small decimals
        
        # Generate random dates for these calls
        call_dates = generate_random_dates(num_points, START_DATE, END_DATE)
        
        for call_date in call_dates:
            # Add jitter to location (spread within cell)
            jittered_x, jittered_y = jitter_point(center_x, center_y)
            
            # Convert to WGS84
            lon, lat = transformer.transform(jittered_x, jittered_y)
            
            # Set time to match the hour
            call_datetime = call_date.replace(hour=hour, minute=random.randint(0, 59))
            
            # Create feature
            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [lon, lat]
                },
                'properties': {
                    'grid_id': int(row['c28992r1000']),
                    'population': int(row['aantal_inwoners']),
                    'timestamp': call_datetime.isoformat(),
                    'date': call_datetime.strftime('%Y-%m-%d'),
                    'time': call_datetime.strftime('%H:%M'),
                    'hour': hour,
                    'period': period,
                    'original_value': float(call_count)
                }
            })
            
            total_calls += 1

print(f"\n   ✅ Processed {cells_processed} Amsterdam grid cells")
print(f"   ✅ Generated {total_calls} individual call points")
print()

# Create GeoJSON
print("💾 Creating GeoJSON...")

# Calculate statistics
periods = {'night': 0, 'morning': 0, 'afternoon': 0, 'evening': 0}
hours = {h: 0 for h in range(24)}

for f in features:
    periods[f['properties']['period']] += 1
    hours[f['properties']['hour']] += 1

geojson = {
    'type': 'FeatureCollection',
    'features': features,
    'metadata': {
        'source': csv_file,
        'date_range': f"{START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}",
        'total_calls': len(features),
        'calls_by_period': periods,
        'calls_by_hour': hours,
        'grid_cells_used': cells_processed,
        'note': 'Points are simulated from grid aggregates with spatial jitter'
    }
}

with open(output_file, 'w') as f:
    json.dump(geojson, f, indent=2)

print(f"✅ Saved to {output_file}")
print()
print("📊 Summary Statistics:")
print(f"   Total simulated calls: {len(features):,}")
print(f"   Source grid cells: {cells_processed:,}")
print(f"   Date range: {START_DATE.strftime('%Y-%m-%d')} to {END_DATE.strftime('%Y-%m-%d')}")
print()
print("   By Time Period:")
for period, count in periods.items():
    pct = (count / len(features) * 100) if features else 0
    print(f"      {period.capitalize():12s}: {count:6,} ({pct:5.1f}%)")
print()
print("   Peak Hours:")
sorted_hours = sorted(hours.items(), key=lambda x: x[1], reverse=True)[:5]
for hour, count in sorted_hours:
    print(f"      Hour {hour:2d}-{(hour+1)%24:2d}: {count:6,} calls")
print()
print(f"✅ Ready to use with amsterdam_ambulance_heatmap.html")
print(f"   Update the fetch URL to: {output_file}")