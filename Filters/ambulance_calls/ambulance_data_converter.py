import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

# ----------------------------
# 1. Load your 1000x1000m grid
# ----------------------------
grid = gpd.read_file("your_grid_file.geojson")  # replace with your file
# Make sure the grid CRS is RD New
grid = grid.to_crs(epsg=28992)

# ----------------------------
# 2. Load ambulance call data
# ----------------------------
calls = pd.read_csv("ambulance_calls.csv")  # replace with your file
# Make sure your CSV has 'x' and 'y' columns in RD New (EPSG:28992)
geometry = [Point(xy) for xy in zip(calls['x'], calls['y'])]
calls_gdf = gpd.GeoDataFrame(calls, geometry=geometry, crs="EPSG:28992")

# ----------------------------
# 3. Spatial join: assign calls to grid cells
# ----------------------------
calls_in_grid = gpd.sjoin(calls_gdf, grid, how="left", predicate='within')

# ----------------------------
# 4. Count calls per grid cell
# ----------------------------
call_counts = calls_in_grid.groupby('index_right').size()
grid['ambulance_calls'] = grid.index.map(call_counts).fillna(0).astype(int)

# ----------------------------
# 5. Save to new file
# ----------------------------
grid.to_file("grid_with_calls.geojson", driver="GeoJSON")
print("Done! GeoJSON with call counts saved.")