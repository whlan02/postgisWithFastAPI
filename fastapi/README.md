# FastAPI Corridors service

This service exposes the **safe corridors** data as a small REST API and is responsible for **importing** the GeoJSON into PostGIS on first run.

## Setup (recommended: Docker Compose)

From the **parent directory** (`postgisWithFastAPI`):

```bash
docker compose up -d
```

This builds and runs the FastAPI app, waits for PostGIS to be healthy, then on first startup:

1. Imports `safe_corridors_prioritized.geojson` into the `safe_corridors` table (EPSG:3414).
2. Fills `safe_corridors_4326` with the same data in EPSG:4326.

Import is **idempotent**: if data already exists, it is skipped.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check; reports app and database status. |
| GET | `/corridors` | Returns all corridors as a **GeoJSON FeatureCollection** (EPSG:4326, all attribute columns). |

## Examples

- Health:  
  `curl http://localhost:8000/health`

- Corridors (GeoJSON):  
  `curl http://localhost:8000/corridors`

Response shape:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "OBJECTID": 9,
        "PLN_AREA_N": "CHOA CHU KANG",
        "priorityID": 1,
        ...
      },
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": [ ... ]
      }
    }
  ]
}
```

You can use this URL in a web map (e.g. Leaflet, Mapbox GL) as a GeoJSON source.

## Running locally (without Docker)

1. Install dependencies: `pip install -r requirements.txt`
2. Start PostGIS (e.g. `docker compose up -d postgis`).
3. Set environment variables (or use defaults):
   - `DATABASE_URL=postgresql://uavuser:uavpass@localhost:5432/uavdb`
   - `GEOJSON_PATH=/path/to/safe_corridors_prioritized.geojson`
4. Run: `uvicorn main:app --reload --host 0.0.0.0 --port 8000`

Ensure the GeoJSON path is readable and points to the same file used in Docker if you want the same data.
