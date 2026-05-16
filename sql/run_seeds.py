""""
Seeder completo — AgroPampa S.A. Datawarehouse
Inserta todas las tablas dimensionales y las nuevas tablas de hechos en cascada.
Orden de inserción respeta el grafo de FKs: hojas → intermedias → principales → fact
"""
import os
import sys
import random
import logging
from datetime import date, timedelta
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

from supabase import create_client

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")
if not URL or not KEY:
    log.error("Faltan SUPABASE_URL / SUPABASE_ANON_KEY en .env")
    sys.exit(1)

client = create_client(URL, KEY)

# ─── utilidades ─────────────────────────────────────────────────────────────

def upsert(table: str, records: list[dict], on_conflict: str) -> list[dict]:
    resp = client.table(table).upsert(records, on_conflict=on_conflict).execute()
    return resp.data or []

def count(table: str) -> int:
    resp = client.table(table).select("*", count="exact").limit(0).execute()
    return resp.count or 0

def skip_if_seeded(table: str, expected: int, fn):
    c = count(table)
    if c >= expected:
        log.info(f"  [skip] {table}: ya tiene {c} filas.")
        return
    log.info(f"  [seed] {table}...")
    fn()
    log.info(f"  [ok]   {table}: {count(table)} filas.")

# ─── 1. dim_provincia ───────────────────────────────────────────────────────
def seed_provincia():
    upsert("dim_provincia", [
        {"id": 1, "nombre": "Buenos Aires"},
        {"id": 2, "nombre": "Santa Fe"},
        {"id": 3, "nombre": "Córdoba"},
    ], on_conflict="id")

# ─── 2. dim_propietario ─────────────────────────────────────────────────────
def seed_propietario():
    upsert("dim_propietario", [
        {"propietario_id": 1, "email": "info@delvalle.com.ar",     "cuit": "30-71234567-8", "telefono": "+54 11 4444-0001", "activo": True},
        {"propietario_id": 2, "email": "admin@losalamos.com.ar",   "cuit": "30-72345678-9", "telefono": "+54 11 4444-0002", "activo": True},
        {"propietario_id": 3, "email": "elpampero@agro.com.ar",    "cuit": "30-73456789-0", "telefono": "+54 11 4444-0003", "activo": True},
        {"propietario_id": 4, "email": "contacto@granosdelsur.ar", "cuit": "30-74567890-1", "telefono": "+54 11 4444-0004", "activo": True},
        {"propietario_id": 5, "email": "gomez.campo@gmail.com",    "cuit": "30-75678901-2", "telefono": "+54 11 4444-0005", "activo": True},
        {"propietario_id": 6, "email": "inversiones@agropampa.ar", "cuit": "30-76789012-3", "telefono": "+54 11 4444-0006", "activo": True},
    ], on_conflict="propietario_id")

# ─── 3. dim_tipo_suelo ──────────────────────────────────────────────────────
TIPO_SUELO = {
    "Franco":           1,
    "Franco limoso":    2,
    "Franco arcilloso": 3,
    "Arcilloso":        4,
    "Arenoso":          5,
    "Vertisol":         6,
}

def seed_tipo_suelo():
    upsert("dim_tipo_suelo", [{"tipo_suelo_id": v, "nombre": k} for k, v in TIPO_SUELO.items()], on_conflict="tipo_suelo_id")

# ─── 4. dim_tipo_maquinaria ─────────────────────────────────────────────────
TIPO_MAQ = {"Sembradora": 1, "Cosechadora": 2, "Pulverizadora": 3, "Tractor": 4}

def seed_tipo_maquinaria():
    upsert("dim_tipo_maquinaria", [{"tipo_maquinaria_id": v, "nombre": k} for k, v in TIPO_MAQ.items()], on_conflict="tipo_maquinaria_id")

# ─── 5. dim_marca_maquinaria ────────────────────────────────────────────────
MARCA_MAQ = {
    "John Deere":  1,
    "Case IH":     2,
    "New Holland": 3,
    "Agrometal":   4,
    "Apache":      5,
    "Metalfor":    6,
    "Jacto":       7,
}

def seed_marca_maquinaria():
    upsert("dim_marca_maquinaria", [{"marca_maquinaria_id": v, "marca_maquinaria": k} for k, v in MARCA_MAQ.items()], on_conflict="marca_maquinaria_id")

# ─── 6. dim_estado_maquinaria ───────────────────────────────────────────────
ESTADO_MAQ = {"Operativo": 1, "En reparación": 2, "Fuera de servicio": 3}

def seed_estado_maquinaria():
    upsert("dim_estado_maquinaria", [{"estado_maquinaria_id": v, "estado": k} for k, v in ESTADO_MAQ.items()], on_conflict="estado_maquinaria_id")

# ─── 7. dim_cultivo ─────────────────────────────────────────────────────────
CULTIVO = {
    "Soja DM 4612 RR":  1,
    "Soja NS 4009 IPRO": 2,
    "Soja Don Mario":   3,
    "Trigo Klein Proteo": 4,
    "Trigo ACA 315":    5,
    "Trigo Buck":       6,
}

def seed_cultivo():
    upsert("dim_cultivo", [{"id_cultivo": v, "cultivo": k} for k, v in CULTIVO.items()], on_conflict="id_cultivo")

# ─── 8. dim_localidad ───────────────────────────────────────────────────────
LOC_DATA = [
    (1, 1, "Pergamino"),
    (2, 1, "Junín"),
    (3, 1, "Nueve de Julio"),
    (4, 2, "Rosario"),
    (5, 2, "Venado Tuerto"),
    (6, 3, "Córdoba Capital"),
    (7, 3, "Río Cuarto"),
]
LOC_NAME_ID = {nombre: lid for lid, _, nombre in LOC_DATA}

def seed_localidad():
    upsert("dim_localidad", [{"id": lid, "provincia_id": prov, "nombre": nombre} for lid, prov, nombre in LOC_DATA], on_conflict="id")

# ─── 9. dim_modelo_maquinaria ──────────────────────────────────────────────
MODELO_DATA = [
    (1, TIPO_MAQ["Sembradora"],    MARCA_MAQ["Agrometal"],   "Monumental 3000"),
    (2, TIPO_MAQ["Sembradora"],    MARCA_MAQ["Apache"],      "Soja 18"),
    (3, TIPO_MAQ["Cosechadora"],   MARCA_MAQ["John Deere"],  "S680"),
    (4, TIPO_MAQ["Cosechadora"],   MARCA_MAQ["New Holland"], "CR9090"),
    (5, TIPO_MAQ["Cosechadora"],   MARCA_MAQ["Case IH"],     "7250 AFS"),
    (6, TIPO_MAQ["Pulverizadora"], MARCA_MAQ["Metalfor"],    "Puelche 4200"),
    (7, TIPO_MAQ["Pulverizadora"], MARCA_MAQ["Jacto"],       "Jacto 3030"),
    (8, TIPO_MAQ["Tractor"],       MARCA_MAQ["John Deere"],  "7215R"),
    (9, TIPO_MAQ["Tractor"],       MARCA_MAQ["Case IH"],     "Puma 185"),
]

def seed_modelo_maquinaria():
    upsert("dim_modelo_maquinaria", [{"modelo_maquinaria_id": mid, "tipo_maquinaria_id": tipo, "marca_maquinaria_id": marca, "nombre_modelo": modelo} for mid, tipo, marca, modelo in MODELO_DATA], on_conflict="modelo_maquinaria_id")

# ─── 10. dim_campo ──────────────────────────────────────────────────────────
CAMPO_DATA = [
    (1, 1, LOC_NAME_ID["Pergamino"],       "Campo Norte"),
    (2, 1, LOC_NAME_ID["Junín"],           "Campo Sur"),
    (3, 2, LOC_NAME_ID["Pergamino"],       "El Tajamar"),
    (4, 3, LOC_NAME_ID["Rosario"],         "La Barrancosa"),
    (5, 3, LOC_NAME_ID["Venado Tuerto"],   "Loma Verde"),
    (6, 4, LOC_NAME_ID["Nueve de Julio"],  "San Cayetano"),
    (7, 5, LOC_NAME_ID["Córdoba Capital"], "La Esperanza"),
    (8, 6, LOC_NAME_ID["Río Cuarto"],      "El Retiro"),
    (9, 6, LOC_NAME_ID["Venado Tuerto"],   "Las Vertientes"),
]
CAMPO_NAME_ID = {nombre: cid for cid, *_, nombre in CAMPO_DATA}

def seed_campo():
    upsert("dim_campo", [{"campo_id": cid, "propietario_id": prop, "localidad_id": loc, "nombre": nombre, "activo": True} for cid, prop, loc, nombre in CAMPO_DATA], on_conflict="campo_id")

# ─── 11. dim_lote ───────────────────────────────────────────────────────────
LOTE_DATA = [
    ( 1, CAMPO_NAME_ID["Campo Norte"],    "Lote 1 - Arroyo",       120.0, TIPO_SUELO["Franco limoso"]),
    ( 2, CAMPO_NAME_ID["Campo Norte"],    "Lote 2 - Laguna",        95.0, TIPO_SUELO["Franco arcilloso"]),
    ( 3, CAMPO_NAME_ID["Campo Norte"],    "Lote 3 - La Rinconada",  80.0, TIPO_SUELO["Arenoso"]),
    ( 4, CAMPO_NAME_ID["Campo Sur"],      "Lote 1 - Norte",        110.0, TIPO_SUELO["Franco limoso"]),
    ( 5, CAMPO_NAME_ID["Campo Sur"],      "Lote 2 - Sur",           95.0, TIPO_SUELO["Arcilloso"]),
    ( 6, CAMPO_NAME_ID["El Tajamar"],     "Lote A",                145.0, TIPO_SUELO["Franco limoso"]),
    ( 7, CAMPO_NAME_ID["El Tajamar"],     "Lote B",                140.0, TIPO_SUELO["Franco arcilloso"]),
    ( 8, CAMPO_NAME_ID["El Tajamar"],     "Lote C",                145.0, TIPO_SUELO["Arcilloso"]),
    ( 9, CAMPO_NAME_ID["La Barrancosa"],  "Lote 1",                200.0, TIPO_SUELO["Vertisol"]),
    (10, CAMPO_NAME_ID["La Barrancosa"],  "Lote 2",                190.0, TIPO_SUELO["Vertisol"]),
    (11, CAMPO_NAME_ID["La Barrancosa"],  "Lote 3",                195.0, TIPO_SUELO["Arenoso"]),
    (12, CAMPO_NAME_ID["La Barrancosa"],  "Lote 4",                185.0, TIPO_SUELO["Franco limoso"]),
    (13, CAMPO_NAME_ID["Loma Verde"],     "Lote 1 - Este",         170.0, TIPO_SUELO["Franco limoso"]),
    (14, CAMPO_NAME_ID["Loma Verde"],     "Lote 2 - Oeste",        170.0, TIPO_SUELO["Franco arcilloso"]),
    (15, CAMPO_NAME_ID["Loma Verde"],     "Lote 3 - Centro",       170.0, TIPO_SUELO["Arcilloso"]),
    (16, CAMPO_NAME_ID["San Cayetano"],   "Lote 1",                190.0, TIPO_SUELO["Franco limoso"]),
    (17, CAMPO_NAME_ID["San Cayetano"],   "Lote 2",                185.0, TIPO_SUELO["Arenoso"]),
    (18, CAMPO_NAME_ID["San Cayetano"],   "Lote 3",                190.0, TIPO_SUELO["Franco limoso"]),
    (19, CAMPO_NAME_ID["San Cayetano"],   "Lote 4",                195.0, TIPO_SUELO["Arcilloso"]),
    (20, CAMPO_NAME_ID["La Esperanza"],   "Lote Norte",            170.0, TIPO_SUELO["Franco limoso"]),
    (21, CAMPO_NAME_ID["La Esperanza"],   "Lote Sur",              170.0, TIPO_SUELO["Arcilloso"]),
    (22, CAMPO_NAME_ID["El Retiro"],      "Lote 1",                275.0, TIPO_SUELO["Franco limoso"]),
    (23, CAMPO_NAME_ID["El Retiro"],      "Lote 2",                275.0, TIPO_SUELO["Vertisol"]),
    (24, CAMPO_NAME_ID["Las Vertientes"], "Lote 1 - Principal",    295.0, TIPO_SUELO["Franco arcilloso"]),
    (25, CAMPO_NAME_ID["Las Vertientes"], "Lote 2 - Secundario",   295.0, TIPO_SUELO["Franco limoso"]),
]

def seed_lote():
    upsert("dim_lote", [{"lote_id": lid, "campo_id": cid, "nombre": nombre, "superficie_ha": sup, "tipo_suelo_id": ts, "activo": True} for lid, cid, nombre, sup, ts in LOTE_DATA], on_conflict="lote_id")

# ─── 12. dim_maquinaria ─────────────────────────────────────────────────────
MAQ_DATA = [
    (1, 2019, 1, ESTADO_MAQ["Operativo"]),       # Monumental 3000
    (2, 2021, 2, ESTADO_MAQ["Operativo"]),       # Soja 18
    (3, 2020, 3, ESTADO_MAQ["Operativo"]),       # S680
    (4, 2018, 4, ESTADO_MAQ["En reparación"]),   # CR9090
    (5, 2022, 5, ESTADO_MAQ["Operativo"]),       # 7250 AFS
    (6, 2020, 6, ESTADO_MAQ["Operativo"]),       # Puelche 4200
    (7, 2021, 7, ESTADO_MAQ["Operativo"]),       # Jacto 3030
    (8, 2019, 8, ESTADO_MAQ["Operativo"]),       # 7215R
    (9, 2021, 9, ESTADO_MAQ["Operativo"]),       # Puma 185
]

def seed_maquinaria():
    upsert("dim_maquinaria", [{"maquinaria_id": mid, "año_fabricacion": anio, "modelo_maquinaria_id": modelo, "estado_maquinaria_id": estado} for mid, anio, modelo, estado in MAQ_DATA], on_conflict="maquinaria_id")

# ─── 13. tipo_operacion (NUEVA TABLA) ───────────────────────────────────────
def seed_tipo_operacion():
    data = [
        {"id": 1, "operacion": "Siembra"},
        {"id": 2, "operacion": "Cosecha"},
        {"id": 3, "operacion": "Pulverización"}
    ]
    client.table("tipo_operacion").upsert(data).execute()

# ─── 14. dim_mediciones_diarias (NUEVA TABLA CASCADA) ───────────────────────
def seed_dim_mediciones_diarias():
    lotes_resp = client.table("dim_lote").select("lote_id").execute()
    data = []
    fecha_inicio = date(2024, 1, 1)
    
    if lotes_resp.data:
        for lote in lotes_resp.data:
            lote_id = lote['lote_id']
            for i in range(30):
                fecha_actual = fecha_inicio + timedelta(days=i)
                data.append({
                    "lote_id": lote_id,
                    "fecha": fecha_actual.isoformat(),
                    "mes": fecha_actual.month,
                    "temp_prom": round(18 + random.random() * 10, 2),
                    "temp_max": round(28 + random.random() * 10, 2),
                    "temp_min": round(10 + random.random() * 10, 2),
                    "humedad_prom": round(60 + random.random() * 20, 2),
                    "precipitacion_mm": round(random.random() * 50, 2),
                    "m3_agua_consumida": round(random.random() * 100, 2)
                })
                
    for i in range(0, len(data), 500):
        client.table("dim_mediciones_diarias").upsert(data[i:i+500]).execute()

# ─── 15. fact_siembra_cosecha (NUEVA TABLA CASCADA) ─────────────────────────
def seed_fact_siembra_cosecha():
    lotes_resp = client.table("dim_lote").select("lote_id, superficie_ha").execute()
    data = []
    if lotes_resp.data:
        for lote in lotes_resp.data:
            superficie = float(lote['superficie_ha'])
            rendimiento = round(3500 * (1 + (random.random() - 0.5) * 0.30), 0)
            data.append({
                "maquinaria_id": 1,
                "id_cultivo": 1, 
                "lote_id": lote['lote_id'],
                "rendimiento_kg_ha": rendimiento,
                "superficie_sembrada_cosechada_ha": superficie,
                "costo_total": round(superficie * 3.5 * 55, 2),
                "precio_venta_tn_prom": 340.00,
                "fecha": "2024-04-15",
                "id_tipo_operacion": 2
            })
            
    client.table("fact_siembra_cosecha").upsert(data).execute()

# ─── MAIN ────────────────────────────────────────────────────────────────────
def main():
    log.info("=== Iniciando seeder AgroPampa DW con Nuevo Modelo ===")
    
    skip_if_seeded("dim_provincia", 3, seed_provincia)
    skip_if_seeded("dim_propietario", 6, seed_propietario)
    skip_if_seeded("dim_tipo_suelo", 6, seed_tipo_suelo)
    skip_if_seeded("dim_tipo_maquinaria", 4, seed_tipo_maquinaria)
    skip_if_seeded("dim_marca_maquinaria", 7, seed_marca_maquinaria)
    skip_if_seeded("dim_estado_maquinaria", 3, seed_estado_maquinaria)
    skip_if_seeded("dim_cultivo", 6, seed_cultivo)
    skip_if_seeded("dim_localidad", 7, seed_localidad)
    skip_if_seeded("dim_modelo_maquinaria", 9, seed_modelo_maquinaria)
    skip_if_seeded("dim_campo", 9, seed_campo)
    skip_if_seeded("dim_lote", 25, seed_lote)
    skip_if_seeded("dim_maquinaria", 9, seed_maquinaria)
    
    # Inyectar las 3 tablas nuevas 
    skip_if_seeded("tipo_operacion", 3, seed_tipo_operacion)
    skip_if_seeded("dim_mediciones_diarias", 1, seed_dim_mediciones_diarias)
    skip_if_seeded("fact_siembra_cosecha", 1, seed_fact_siembra_cosecha)

if __name__ == '__main__':
    main()