"""
Seeder completo — AgroPampa S.A. Datawarehouse
Inserta todas las tablas dimensionales y fact_produccion en Supabase
vía REST API (supabase-py). Los IDs son explícitos porque las columnas
PK son INTEGER sin secuencia automática.

Orden de inserción respeta el grafo de FKs:
  hojas → intermedias → principales → fact

Correr desde la raíz del repo:
    python sql/run_seeds.py
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
    upsert("dim_tipo_suelo",
        [{"tipo_suelo_id": v, "nombre": k} for k, v in TIPO_SUELO.items()],
        on_conflict="tipo_suelo_id")


# ─── 4. dim_tipo_maquinaria ─────────────────────────────────────────────────

TIPO_MAQ = {"Sembradora": 1, "Cosechadora": 2, "Pulverizadora": 3, "Tractor": 4}

def seed_tipo_maquinaria():
    upsert("dim_tipo_maquinaria",
        [{"tipo_maquinaria_id": v, "nombre": k} for k, v in TIPO_MAQ.items()],
        on_conflict="tipo_maquinaria_id")


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
    upsert("dim_marca_maquinaria",
        [{"marca_maquinaria_id": v, "marca_maquinaria": k} for k, v in MARCA_MAQ.items()],
        on_conflict="marca_maquinaria_id")


# ─── 6. dim_estado_maquinaria ───────────────────────────────────────────────

ESTADO_MAQ = {"Operativo": 1, "En reparación": 2, "Fuera de servicio": 3}

def seed_estado_maquinaria():
    upsert("dim_estado_maquinaria",
        [{"estado_maquinaria_id": v, "estado": k} for k, v in ESTADO_MAQ.items()],
        on_conflict="estado_maquinaria_id")


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
    upsert("dim_cultivo",
        [{"id_cultivo": v, "cultivo": k} for k, v in CULTIVO.items()],
        on_conflict="id_cultivo")


# ─── 8. dim_tiempo ──────────────────────────────────────────────────────────

def seed_tiempo():
    records = []
    inicio = date(2022, 7, 1)
    for i in range(36):
        # Avanzar i meses desde julio 2022
        month = (inicio.month - 1 + i) % 12 + 1
        year  = inicio.year + (inicio.month - 1 + i) // 12
        d     = date(year, month, 1)
        # Semana ISO del primer día del mes
        iso_week = d.isocalendar()[1]
        records.append({
            "tiempo_id": i + 1,
            "fecha":     d.isoformat(),
            "dia":       1,
            "semana":    iso_week,
            "mes":       month,
            "trimestre": (month - 1) // 3 + 1,
            "año":       year,
        })
    upsert("dim_tiempo", records, on_conflict="tiempo_id")


def build_tiempo_map() -> dict[date, int]:
    rows = client.table("dim_tiempo").select("tiempo_id,fecha").execute().data
    result = {}
    for r in rows:
        f = date.fromisoformat(r["fecha"])
        result[f] = r["tiempo_id"]
    return result


# ─── 9. dim_localidad ───────────────────────────────────────────────────────

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
    upsert("dim_localidad",
        [{"id": lid, "provincia_id": prov, "nombre": nombre}
         for lid, prov, nombre in LOC_DATA],
        on_conflict="id")


# ─── 10. dim_modelo_maquinaria ──────────────────────────────────────────────

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
    upsert("dim_modelo_maquinaria",
        [{"modelo_maquinaria_id": mid, "tipo_maquinaria_id": tipo,
          "marca_maquinaria_id": marca, "nombre_modelo": modelo}
         for mid, tipo, marca, modelo in MODELO_DATA],
        on_conflict="modelo_maquinaria_id")


# ─── 11. dim_campo ──────────────────────────────────────────────────────────

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
    upsert("dim_campo",
        [{"campo_id": cid, "propietario_id": prop, "localidad_id": loc,
          "nombre": nombre, "activo": True}
         for cid, prop, loc, nombre in CAMPO_DATA],
        on_conflict="campo_id")


# ─── 12. dim_lote ───────────────────────────────────────────────────────────

LOTE_DATA = [
    # (lote_id, campo_id, nombre, superficie_ha, tipo_suelo_id)
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
    upsert("dim_lote",
        [{"lote_id": lid, "campo_id": cid, "nombre": nombre,
          "superficie_ha": sup, "tipo_suelo_id": ts, "activo": True}
         for lid, cid, nombre, sup, ts in LOTE_DATA],
        on_conflict="lote_id")


# ─── 13. dim_maquinaria ─────────────────────────────────────────────────────

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
    upsert("dim_maquinaria",
        [{"maquinaria_id": mid, "año_fabricacion": anio,
          "modelo_maquinaria_id": modelo, "estado_maquinaria_id": estado}
         for mid, anio, modelo, estado in MAQ_DATA],
        on_conflict="maquinaria_id")


# ─── 14. fact_produccion ────────────────────────────────────────────────────
# 150 filas: 25 lotes × 3 campañas × 2 cultivos (soja-abril / trigo-noviembre)

REND_BASE = {
    TIPO_SUELO["Franco"]:           3700,
    TIPO_SUELO["Franco limoso"]:    3800,
    TIPO_SUELO["Franco arcilloso"]: 3500,
    TIPO_SUELO["Arcilloso"]:        3200,
    TIPO_SUELO["Arenoso"]:          2600,
    TIPO_SUELO["Vertisol"]:         4100,
}

CAMPAÑAS = [
    # (anio_cosecha_soja, mes_cosecha_soja, anio_cosecha_trigo, mes_cosecha_trigo, factor)
    (2023, 4,  2022, 11, 1.00),  # 2022/23
    (2024, 4,  2023, 11, 0.82),  # 2023/24 sequía
    (2025, 4,  2024, 11, 1.07),  # 2024/25
]

def seed_fact_produccion(tiempo_map: dict[date, int]):
    records = []
    fact_id = 1

    for lote_id, campo_id, nombre, superficie, ts_id in LOTE_DATA:
        rend_base = REND_BASE[ts_id]

        for anio_soja, mes_soja, anio_trigo, mes_trigo, factor in CAMPAÑAS:
            # ── SOJA (cultivos 1-3, cosecha abril) ──────────────────
            fecha_soja  = date(anio_soja, mes_soja, 1)
            tiempo_soja = tiempo_map.get(fecha_soja)
            if tiempo_soja:
                rend = rend_base * factor * (1 + (random.random() - 0.5) * 0.30)
                sup_cos = superficie * (0.85 + random.random() * 0.10)
                records.append({
                    "id":                      fact_id,
                    "maquinaria_id":           ((lote_id - 1) % 9) + 1,
                    "id_cultivo":              ((lote_id - 1) % 3) + 1,   # 1-3 soja
                    "lote_id":                 lote_id,
                    "tiempo_id":               tiempo_soja,
                    "rendimiento_kg_ha":       round(rend, 1),
                    "superficie_cosechada_ha": round(sup_cos, 1),
                    "costo_total":             round(sup_cos * (rend / 1000) * 55, 2),
                    "previo_venta_tn_prom":    round(340 * (0.90 + random.random() * 0.20), 2),
                })
                fact_id += 1

            # ── TRIGO (cultivos 4-6, cosecha noviembre) ──────────────
            fecha_trigo  = date(anio_trigo, mes_trigo, 1)
            tiempo_trigo = tiempo_map.get(fecha_trigo)
            if tiempo_trigo:
                rend = rend_base * 0.95 * factor * (1 + (random.random() - 0.5) * 0.30)
                sup_cos = superficie * (0.85 + random.random() * 0.10)
                records.append({
                    "id":                      fact_id,
                    "maquinaria_id":           ((lote_id - 1) % 9) + 1,
                    "id_cultivo":              ((lote_id - 1) % 3) + 4,   # 4-6 trigo
                    "lote_id":                 lote_id,
                    "tiempo_id":               tiempo_trigo,
                    "rendimiento_kg_ha":       round(rend, 1),
                    "superficie_cosechada_ha": round(sup_cos, 1),
                    "costo_total":             round(sup_cos * (rend / 1000) * 55, 2),
                    "previo_venta_tn_prom":    round(260 * (0.90 + random.random() * 0.20), 2),
                })
                fact_id += 1

    upsert("fact_produccion", records, on_conflict="id")
    return len(records)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main():
    log.info("=== Iniciando seeder AgroPampa DW ===")

    skip_if_seeded("dim_provincia",        3,  seed_provincia)
    skip_if_seeded("dim_propietario",      6,  seed_propietario)
    skip_if_seeded("dim_tipo_suelo",       6,  seed_tipo_suelo)
    skip_if_seeded("dim_tipo_maquinaria",  4,  seed_tipo_maquinaria)
    skip_if_seeded("dim_marca_maquinaria", 7,  seed_marca_maquinaria)
    skip_if_seeded("dim_estado_maquinaria",3,  seed_estado_maquinaria)
    skip_if_seeded("dim_cultivo",          6,  seed_cultivo)
    skip_if_seeded("dim_tiempo",           36, seed_tiempo)
    skip_if_seeded("dim_localidad",        7,  seed_localidad)
    skip_if_seeded("dim_modelo_maquinaria",9,  seed_modelo_maquinaria)
    skip_if_seeded("dim_campo",            9,  seed_campo)
    skip_if_seeded("dim_lote",             25, seed_lote)
    skip_if_seeded("dim_maquinaria",       9,  seed_maquinaria)

    # fact_produccion necesita tiempo_map para resolver tiempo_id por fecha
    c_fact = count("fact_produccion")
    if c_fact >= 150:
        log.info(f"  [skip] fact_produccion: ya tiene {c_fact} filas.")
    else:
        log.info("  [seed] fact_produccion...")
        tiempo_map = build_tiempo_map()
        n = seed_fact_produccion(tiempo_map)
        log.info(f"  [ok]   fact_produccion: {n} filas.")

    log.info("=== Seeder completado ===")

    # Resumen final
    tablas = [
        "dim_provincia","dim_propietario","dim_tipo_suelo","dim_tipo_maquinaria",
        "dim_marca_maquinaria","dim_estado_maquinaria","dim_cultivo","dim_tiempo",
        "dim_localidad","dim_modelo_maquinaria","dim_campo","dim_lote",
        "dim_maquinaria","dim_clima","fact_produccion",
    ]
    log.info("─── Conteo final por tabla ───────────────────")
    for t in tablas:
        log.info(f"  {t:<30} {count(t):>5} filas")


if __name__ == "__main__":
    main()
