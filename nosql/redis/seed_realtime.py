"""
Carga el "estado actual" de los sensores en Redis.

A diferencia de Mongo, que guarda el histórico crudo, Redis solo tiene la
ÚLTIMA lectura de cada lote. Es lo que mira el sistema de riego automático
para decidir si hay que abrir la canilla o no — necesita respuesta en
milisegundos, no se puede ir a buscar a la base SQL.

Correr con:
    python nosql/redis/seed_realtime.py

    
1. ¿POR QUÉ TEMPORAL?: Usamos un TTL (Time To Live) de 3600s (1 hora). 
   Esto asegura que el Dashboard solo muestre datos frescos. Si un sensor 
   falla y deja de reportar, la llave expira y el sistema detecta que el 
   lote está "Offline" en lugar de mostrar valores viejos.

2. COMPORTAMIENTO AL RE-EJECUTAR: El comando SET de Redis es destructivo. 
   Si corres este script de nuevo, se sobrescriben los valores anteriores 
   y se reinicia el reloj del TTL. Ideal para simular cambios de estado 
   en vivo durante una demo.

3. FAST DATA vs. SLOW DATA:
   - Redis: Capa de velocidad. Respuesta en <1ms. Sin historial.
   - MongoDB: Capa de persistencia cruda. Historial completo (horas).
   - Supabase: Capa de analítica. Datos agregados (días) para KPIs.

4. LÓGICA DE SIMULACIÓN: Se utiliza random.gauss para evitar valores lineales
   y simular una distribución normal de temperatura/humedad según el tipo 
   de suelo definido en LOTES.
"""
import os
import sys
import random
import logging
import redis
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

HUMEDAD_BASE = {
    "Franco limoso":    66.0,
    "Franco arcilloso": 64.0,
    "Arcilloso":        62.0,
    "Arenoso":          54.0,
    "Vertisol":         70.0,
}

LOTES = [
    (1,  "Lote C",                "Arcilloso"),
    (2,  "Lote B",                "Franco arcilloso"),
    (3,  "Lote A",                "Franco limoso"),
    (4,  "Lote 3 - La Rinconada", "Arenoso"),
    (5,  "Lote 2 - Laguna",       "Franco arcilloso"),
    (6,  "Lote 1 - Arroyo",       "Franco limoso"),
    (7,  "Lote 2 - Sur",          "Arcilloso"),
    (8,  "Lote 1 - Norte",        "Franco limoso"),
    (9,  "Lote 4 (San Cayetano)", "Arcilloso"),
    (10, "Lote 3 (San Cayetano)", "Franco limoso"),
    (11, "Lote 2 (San Cayetano)", "Arenoso"),
    (12, "Lote 1 (San Cayetano)", "Franco limoso"),
    (13, "Lote 4 (Barrancosa)",   "Franco limoso"),
    (14, "Lote 3 (Barrancosa)",   "Arenoso"),
    (15, "Lote 2 (Barrancosa)",   "Vertisol"),
    (16, "Lote 1 (Barrancosa)",   "Vertisol"),
    (17, "Lote 2 - Secundario",   "Franco limoso"),
    (18, "Lote 1 - Principal",    "Franco arcilloso"),
    (19, "Lote 3 - Centro",       "Arcilloso"),
    (20, "Lote 2 - Oeste",        "Franco arcilloso"),
    (21, "Lote 1 - Este",         "Franco limoso"),
    (22, "Lote Sur",              "Arcilloso"),
    (23, "Lote Norte",            "Franco limoso"),
    (24, "Lote 2 (El Retiro)",    "Vertisol"),
    (25, "Lote 1 (El Retiro)",    "Franco limoso"),
]

UMBRAL_RIEGO = 45.0


def run_seed():
    url = os.getenv("REDIS_URL")
    if not url:
        logger.error("Falta REDIS_URL en .env. Salimos.")
        sys.exit(1)

    r = redis.Redis.from_url(url, decode_responses=True)
    r.ping()
    logger.info("Conectado a Redis.")

    total_keys = 0
    riegos_on = 0

    for lote_id, nombre, tipo_suelo in LOTES:
        humedad_base = HUMEDAD_BASE.get(tipo_suelo, 62.0)

        humedad = round(humedad_base + random.gauss(0, 4.0), 2)
        temp    = round(18.0 + random.gauss(0, 2.5), 2)

        estado_riego = "ON" if humedad < UMBRAL_RIEGO else "OFF"
        if estado_riego == "ON":
            riegos_on += 1

        ttl = 3600

        r.set(f"sensor:{lote_id}:humedad",     humedad,      ex=ttl)
        r.set(f"sensor:{lote_id}:temperatura", temp,         ex=ttl)
        r.set(f"riego:{lote_id}:estado",       estado_riego, ex=ttl)
        total_keys += 3

        logger.info(
            f"  lote_id={lote_id:2d} ({tipo_suelo}): "
            f"humedad={humedad}% temp={temp}°C → riego {estado_riego}"
        )

    logger.info(f"Listo. {total_keys} keys cargadas, {riegos_on} riegos encendidos.")
    logger.info("Patrón de claves: sensor:{id}:humedad | sensor:{id}:temperatura | riego:{id}:estado")


if __name__ == "__main__":
    run_seed()
