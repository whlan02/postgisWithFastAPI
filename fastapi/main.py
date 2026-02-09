import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor


DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://uavuser:uavpass@localhost:5432/uavdb")
GEOJSON_PATH = os.environ.get("GEOJSON_PATH", "/data/safe_corridors_prioritized.geojson")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from import_data import run_import
    try:
        run_import(DATABASE_URL, GEOJSON_PATH)
    except Exception as e:
        print(f"Startup import warning: {e}")
    yield
    # no shutdown needed


app = FastAPI(title="Corridors API", lifespan=lifespan)

# CORS for local frontend dev 
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    try:
        with psycopg2.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        db = "ok"
    except Exception as e:
        db = str(e)
    return {"status": "ok", "database": db}


def get_corridors_geojson():
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT id, "OBJECTID", "PLN_AREA_N", "PLN_AREA_C", "CA_IND", "REGION_N", "REGION_C",
                    "INC_CRC", "FMEL_UPD_D", "SHAPE.AREA", "SHAPE.LEN", "Total_Population",
                    "Total_Males", "Total_Females", "LabourForce_Total_Total", "LabourForce_Total_Males",
                    "LabourForce_Total_Females", "LabourForce_Employed_Total", "LabourForce_Employed_Males",
                    "LabourForce_Employed_Females", "LabourForce_Unemployed_Total", "LabourForce_Unemployed_Males",
                    "LabourForce_Unemployed_Females", "OutsidetheLabourForce_Total", "OutsidetheLabourForce_Males",
                    "OutsidetheLabourForce_Females", "Area_km2", "Pop_Density", "priorityID",
                    ST_AsGeoJSON(geom)::json AS geom
                FROM safe_corridors_4326
                ORDER BY id
            """)
            rows = cur.fetchall()
    features = []
    for r in rows:
        geom = r.pop("geom", None)
        r.pop("id", None)
        if geom is None:
            continue
        features.append({
            "type": "Feature",
            "properties": dict(r),
            "geometry": geom,
        })
    return {"type": "FeatureCollection", "features": features}


@app.get("/corridors")
def corridors():
    return JSONResponse(content=get_corridors_geojson())
