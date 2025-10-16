import pandas as pd
import geopandas as gpd

# Load CSV with ambulance data
df = pd.read_csv("spatiotemporal_grid_time_step=4.csv")

# Load grid GeoJSON or shapefile
grid = gpd.read_file("grid_cells_1km.geojson")  # or .shp

# Merge on grid ID
merged = grid.merge(df, left_on="grid_id", right_on="c28992r1000")

# Optionally, pick one column to visualize, e.g., Total
merged = merged[["geometry", "Total"]]

# Save as GeoJSON for Mapbox
merged.to_file("ambulance_calls.geojson", driver="GeoJSON")