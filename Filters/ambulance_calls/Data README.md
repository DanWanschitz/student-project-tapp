# Data README

## Ambulance Call Data

- **File(s)**: `spatiotemporal_grid_time_step=1.csv`, `spatiotemporal_grid_time_step=4.csv`, `scaled_spatio_temporal_grid_time_step=4.csv`
- **Description**: This dataset contains hourly ambulance call data, aggregated and spatially allocated to 1 km by 1 km grid cells for The Hague, Rotterdam, and Amsterdam. It covers three autumn seasons from 2017 to 2019. The `scaled_spatio_temporal_grid_time_step=4.csv` file contains scaled values of the ambulance calls, adjusting for certain factors.
- **Attributes**:
  - **`index`** (first column) or **`c28992r1000`**: Identifier for the 1 km by 1 km grid cell.
  - **`0-4`, ..., `20-0`**: Columns representing the number of ambulance calls in the grid cell for each 4-hour time step throughout the day.
  - **`Total`**: The sum of the ambulance calls recorded over all time periods for the specific grid cell.

For detailed information on other datasets, please refer to the official documentation on the dedicated web pages.

## Socio-Demographic Grid

- **Data Source**: [CBS Socio-Demographic Grid (500m x 500m) with Statistics](https://www.cbs.nl/nl-nl/dossier/nederland-regionaal/geografische-data/kaart-van-500-meter-bij-500-meter-met-statistieken)

## City and District Boundaries

- **Data Source**: [CBS City and District Boundaries (2023)](https://www.cbs.nl/nl-nl/dossier/nederland-regionaal/geografische-data/wijk-en-buurtkaart-2023)
