# PostGIS container

This directory holds the **PostGIS** service used by the Corridors API.

## Role

- Runs [PostGIS](https://postgis.net/) (PostgreSQL + spatial extension) in Docker.
- Database and tables are created by the **docker-compose** stack; this folder only provides **init scripts** and documentation.

## Database parameters (defaults)

| Parameter | Value |
|-----------|--------|
| Database  | `uavdb` |
| User      | `uavuser` |
| Password  | `uavpass` |
| Port      | `5432` (mapped on host when using compose) |

## Volumes

- **Data**: A named volume `postgis_data` persists PostgreSQL data so restarts do not lose data.
- **Init scripts**: The `init/` folder is mounted into the container as `/docker-entrypoint-initdb.d`. Scripts there run only when the database is initialized for the first time (empty volume).

## Init scripts

- `01-extension.sql` – enables the PostGIS extension.
- `02-schema.sql` – creates tables and indexes:
  - **corridors_2d** / **corridors_2d_4326**: 2D safe corridors (EPSG:3414 and EPSG:4326).
  - **network_3d** / **network_3d_4326**: 3D merged network (EPSG:3414 and EPSG:4326).

Data is loaded into these tables by the **FastAPI** service on first startup (see `fastapi/README.md`).

## Running PostGIS

You do **not** need to run PostGIS alone for normal use. From the **parent directory** (`postgisWithFastAPI`), run:

```bash
docker compose up -d
```

This starts both the PostGIS and FastAPI containers. See the parent directory README for full setup and verification.
