import os
import pandas as pd
import geopandas as gpd

# --- Paths ---
script_dir = os.path.dirname(__file__)
csv_path = os.path.join(script_dir, "spatiotemporal_grid_time_step=4.csv")

# Pick the correct 1 km grid JSON file
# Adjust if needed; here we take the first 1000x1000*.json found
grid_files = [f for f in os.listdir(script_dir) if f.startswith("1000x1000") and f.endswith(".json")]
if not grid_files:
    raise FileNotFoundError("No 1000x1000 JSON grid file found in folder.")
grid_path = os.path.join(script_dir, grid_files[0])

# --- Load data ---
df = pd.read_csv(csv_path)
grid = gpd.read_file(grid_path)

# --- Detect possible ID columns in grid ---
possible_id_cols = [col for col in grid.columns if "c" in col or "id" in col.lower()]
if not possible_id_cols:
    raise KeyError("No suitable grid ID column found in JSON.")
grid_id_col = possible_id_cols[0]  # pick first match
print(f"Using grid ID column: {grid_id_col}")

# --- Merge CSV with grid ---
merged = grid.merge(df, left_on=grid_id_col, right_on="c28992r1000")

# --- Keep geometry + 'Total' column for Mapbox ---
if "Total" not in merged.columns:
    raise KeyError("CSV does not contain 'Total' column")
output_gdf = merged[["geometry", "Total"]]

# --- Export GeoJSON ---
output_path = os.path.join(script_dir, "ambulance_calls.geojson")
output_gdf.to_file(output_path, driver="GeoJSON")

print(f"Mapbox-ready GeoJSON exported to: {output_path}")