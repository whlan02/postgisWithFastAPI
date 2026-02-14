# FastAPI Corridors service

This service exposes **2D corridors**, **3D network** (GeoJSON from PostGIS), and **3D Tiles** (static files). It imports the two GeoJSON files into PostGIS on first run.

## Setup (recommended: Docker Compose)

From the **parent directory** (`postgisWithFastAPI`):

```bash
docker compose up -d --build
```

If you previously ran the old version, use:

```bash
docker compose down -v
docker compose up -d --build
```

On first startup the app:

1. Imports `2D_safe_corridors_prioritized.geojson` into `corridors_2d` (EPSG:3414) and fills `corridors_2d_4326`.
2. Imports `3D_merged_network.geojson` into `network_3d` (EPSG:3414) and fills `network_3d_4326`.

Import is **idempotent**: if data already exists in a table, it is skipped.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check; reports app and database status. |
| GET | `/2d-corridors` | 2D safe corridors as a **GeoJSON FeatureCollection** (EPSG:4326). |
| GET | `/3d-network` | 3D merged network as a **GeoJSON FeatureCollection** (EPSG:4326). |
| Static | `/3dtiles/` | 3D Tiles (e.g. `http://localhost:8000/3dtiles/tileset.json` for Cesium). |

## Examples

- Health:  
  `curl http://localhost:8000/health`

- 2D corridors (GeoJSON):  
  `curl http://localhost:8000/2d-corridors`

- 3D network (GeoJSON):  
  `curl http://localhost:8000/3d-network`

- 3D Tiles (Cesium):  
  `Cesium.Cesium3DTileset.fromUrl('http://localhost:8000/3dtiles/tileset.json')`

GeoJSON responses have the usual `FeatureCollection` shape with `features[].properties` and `features[].geometry`.

## Running locally (without Docker)

1. Install dependencies: `pip install -r requirements.txt`
2. Start PostGIS (e.g. `docker compose up -d postgis`).
3. Set environment variables (or use defaults):
   - `DATABASE_URL=postgresql://uavuser:uavpass@localhost:5432/uavdb`
   - `GEOJSON_2D_PATH=/path/to/2D_safe_corridors_prioritized.geojson`
   - `GEOJSON_3D_PATH=/path/to/3D_merged_network.geojson`
   - `TILES_DIR=/path/to/tiles`
4. Run: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

Ensure the GeoJSON paths and tiles directory are readable.
