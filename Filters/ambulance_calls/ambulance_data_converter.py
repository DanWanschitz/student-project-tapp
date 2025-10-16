import pandas as pd
import geopandas as gpd
import os

script_dir = os.path.dirname(__file__)
csv_path = os.path.join(script_dir, "spatiotemporal_grid_time_step=4.csv")
grid_path = os.path.join(script_dir, "1000x1000.json")  # <- use one of your JSON files

# Load data
df = pd.read_csv(csv_path)
grid = gpd.read_file(grid_path)

# Merge CSV values with grid (assuming a column in grid matches CSV grid ID)
merged = grid.merge(df, left_on="grid_id", right_on="c28992r1000")  # adjust column names if needed

# Export for Mapbox
merged.to_file(os.path.join(script_dir, "ambulance_calls.geojson"), driver="GeoJSON")