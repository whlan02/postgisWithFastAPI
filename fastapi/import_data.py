"""
Idempotent import: load GeoJSON into safe_corridors (EPSG:3414), then
populate safe_corridors_4326 via ST_Transform. Skips if tables already have data.
"""
import json
import time
from pathlib import Path

import psycopg2

# Attribute columns in table order (no id, no geom)
ATTR_COLS = [
    "OBJECTID", "PLN_AREA_N", "PLN_AREA_C", "CA_IND", "REGION_N", "REGION_C",
    "INC_CRC", "FMEL_UPD_D", "SHAPE.AREA", "SHAPE.LEN", "Total_Population",
    "Total_Males", "Total_Females", "LabourForce_Total_Total", "LabourForce_Total_Males",
    "LabourForce_Total_Females", "LabourForce_Employed_Total", "LabourForce_Employed_Males",
    "LabourForce_Employed_Females", "LabourForce_Unemployed_Total", "LabourForce_Unemployed_Males",
    "LabourForce_Unemployed_Females", "OutsidetheLabourForce_Total", "OutsidetheLabourForce_Males",
    "OutsidetheLabourForce_Females", "Area_km2", "Pop_Density", "priorityID",
]


def wait_db(conninfo: str, timeout_sec: float = 60, interval_sec: float = 2) -> None:
    deadline = time.monotonic() + timeout_sec
    while time.monotonic() < deadline:
        try:
            with psycopg2.connect(conninfo) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            return
        except Exception:
            time.sleep(interval_sec)
    raise RuntimeError("Database did not become ready in time")


def has_data(conn) -> bool:
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM safe_corridors LIMIT 1")
        return cur.fetchone() is not None


def load_and_import(conn, geojson_path: str) -> None:
    path = Path(geojson_path)
    if not path.is_file():
        raise FileNotFoundError(f"GeoJSON not found: {geojson_path}")
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    features = data.get("features") or []
    if not features:
        return

    col_list = ", ".join(f'"{c}"' for c in ATTR_COLS)
    placeholders = ", ".join(["%s"] * len(ATTR_COLS)) + ", ST_SetSRID(ST_Multi(ST_GeomFromGeoJSON(%s)), 3414)"
    insert_sql = f'INSERT INTO safe_corridors ({col_list}, geom) VALUES ({placeholders})'

    with conn.cursor() as cur:
        for f in features:
            props = f.get("properties") or {}
            geom_str = json.dumps(f.get("geometry"))
            row = [props.get(c) for c in ATTR_COLS] + [geom_str]
            cur.execute(insert_sql, row)
    conn.commit()

    # Populate 4326 table from 3414
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO safe_corridors_4326 (
                "OBJECTID", "PLN_AREA_N", "PLN_AREA_C", "CA_IND", "REGION_N", "REGION_C",
                "INC_CRC", "FMEL_UPD_D", "SHAPE.AREA", "SHAPE.LEN", "Total_Population",
                "Total_Males", "Total_Females", "LabourForce_Total_Total", "LabourForce_Total_Males",
                "LabourForce_Total_Females", "LabourForce_Employed_Total", "LabourForce_Employed_Males",
                "LabourForce_Employed_Females", "LabourForce_Unemployed_Total", "LabourForce_Unemployed_Males",
                "LabourForce_Unemployed_Females", "OutsidetheLabourForce_Total", "OutsidetheLabourForce_Males",
                "OutsidetheLabourForce_Females", "Area_km2", "Pop_Density", "priorityID", geom
            )
            SELECT
                "OBJECTID", "PLN_AREA_N", "PLN_AREA_C", "CA_IND", "REGION_N", "REGION_C",
                "INC_CRC", "FMEL_UPD_D", "SHAPE.AREA", "SHAPE.LEN", "Total_Population",
                "Total_Males", "Total_Females", "LabourForce_Total_Total", "LabourForce_Total_Males",
                "LabourForce_Total_Females", "LabourForce_Employed_Total", "LabourForce_Employed_Males",
                "LabourForce_Employed_Females", "LabourForce_Unemployed_Total", "LabourForce_Unemployed_Males",
                "LabourForce_Unemployed_Females", "OutsidetheLabourForce_Total", "OutsidetheLabourForce_Males",
                "OutsidetheLabourForce_Females", "Area_km2", "Pop_Density", "priorityID",
                ST_Transform(geom, 4326)
            FROM safe_corridors
        """)
    conn.commit()


def run_import(database_url: str, geojson_path: str) -> None:
    wait_db(database_url)
    with psycopg2.connect(database_url) as conn:
        if has_data(conn):
            return
        load_and_import(conn, geojson_path)
