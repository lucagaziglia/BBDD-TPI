"""
histórico

documentos (25 lotes × cantida de días × 24 lecturas/día) una lectura porhora

Estructura de documento:
    {
        "lote_id": int,
        "timestamp": string (ISO 8601),
        "temp": float,
        "humedad_suelo": float,
        "precipitacion": float,
        "agua": float
    }

Correr con:
    python nosql/cassandra/seed_sensors.py
"""
import os
import sys
import random
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Permite importar el helper de conexión desde el extractor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from etl.extractors.cassandra_extractor import connect_astradb  # noqa: E402

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# 25 lotes
LOTES = list(range(1, 26))

# Permite importar el helper de conexión desde el extractor
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from etl.extractors.cassandra_extractor import connect_astradb  # noqa: E402

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Configuración básica del proyecto
LOTES = list(range(1, 26))

HUMEDAD_BASE = {
    "Franco": 60.0,
    "Arcilloso": 70.0,
    "Arenoso": 45.0,
    "Predeterminado": 55.0
}

def generar_lecturas(
    lote_id: int, 
    tipo_suelo: str, 
    fecha_inicio: datetime, 
    fecha_fin: datetime,
    eventos: list = None
) -> list[dict]:
    """Genera lecturas crudas horarias simulando estados climáticos."""
    if eventos is None:
        eventos = []
        
    docs = []
    humedad_base = HUMEDAD_BASE.get(tipo_suelo, HUMEDAD_BASE["Predeterminado"])
    tiempo_actual = fecha_inicio
    
    while tiempo_actual <= fecha_fin:
        estado_clima = "normal"
        
        # Revisamos si hay algún evento activo para este lote en esta hora
        for evento in eventos:
            if evento["lote_id"] == lote_id and evento["inicio"] <= tiempo_actual <= evento["fin"]:
                estado_clima = evento["tipo"]
                break
        
        # Lógica de generación climática
        if estado_clima == "sequia":
            humedad = random.uniform(30.0, 44.0)
            temp = random.uniform(30.0, 38.0)
            precipitacion = 0.0
        elif estado_clima == "inundacion":
            humedad = random.uniform(85.0, 100.0)
            temp = random.uniform(15.0, 22.0)
            precipitacion = random.uniform(30.0, 80.0)
        else:
            humedad = random.uniform(humedad_base - 5, humedad_base + 5)
            temp = random.uniform(15.0, 28.0)
            # 10% de probabilidad de lluvia ligera
            precipitacion = random.choices([0.0, random.uniform(2.0, 15.0)], weights=[0.9, 0.1])[0]

        docs.append({
            "lote_id": lote_id,
            "timestamp": tiempo_actual.replace(microsecond=0).isoformat() + "Z",
            "temp": round(temp, 2),
            "humedad_suelo": round(humedad, 2),
            "precipitacion": round(precipitacion, 2),
            "agua": round(random.uniform(5.0, 30.0), 2)
        })
        
        tiempo_actual += timedelta(hours=1)

    return docs


def generate_iot_data(days: int = 30, batch_size: int = 100):
    """Conecta a Astra DB, limpia la colección e inserta las lecturas en lotes controlados."""
    collection = connect_astradb("sensor_readings")
    if collection is None:
        logger.error("No se pudo conectar a Astra DB. Verificá las variables de entorno.")
        sys.exit(1)

    logger.info("Limpiando colección sensor_readings de Astra DB...")
    collection.delete_many({})

    fecha_fin_global = datetime.utcnow()
    fecha_inicio_global = fecha_fin_global - timedelta(days=days)
    
    # Simulación de eventos controlados para la demo
    eventos_simulados = [
        {
           "lote_id": 1,
           "tipo": "sequia",
           "inicio": fecha_fin_global - timedelta(days=15),
           "fin": fecha_fin_global
        }
        ,
        {
           "lote_id": 8,
           "tipo": "sequia",
           "inicio": fecha_fin_global - timedelta(days=20), 
           "fin": fecha_fin_global
        }
    ]   
    
    total_insertado = 0
    logger.info(f"Iniciando generación de datos históricos por lote...")

    # Corregido: Iteramos directamente sobre los IDs del array LOTES
    for lote_id in LOTES:
        # Asignamos un tipo de suelo ficticio basado en el ID para variar los datos
        tipo_suelo = "Franco" if lote_id % 2 == 0 else "Arenoso"
        
        # Generamos todas las lecturas en memoria para este lote
        lecturas_lote = generar_lecturas(
            lote_id=lote_id,
            tipo_suelo=tipo_suelo,
            fecha_inicio=fecha_inicio_global,
            fecha_fin=fecha_fin_global,
            eventos=eventos_simulados
        )
        
        # Procesamos e insertamos en Astra DB usando batches acotados
        batch = []
        for doc in lecturas_lote:
            batch.append(doc)
            if len(batch) >= batch_size:
                try:
                    collection.insert_many(batch)
                    total_insertado += len(batch)
                    batch = []
                except Exception as e:
                    logger.error(f"Error insertando batch para lote {lote_id}: {e}")
                    return

        # Insertamos el remanente si quedó algo en el último batch
        if batch:
            try:
                collection.insert_many(batch)
                total_insertado += len(batch)
            except Exception as e:
                logger.error(f"Error en batch final del lote {lote_id}: {e}")
                return

        logger.info(f"  lote_id={lote_id:2d}: insertadas {len(lecturas_lote)} lecturas ({tipo_suelo})")

    logger.info(f"Exito. {total_insertado} documentos guardados.")


if __name__ == "__main__":
    generate_iot_data(days=30)

# def generate_iot_data(days: int = 30, batch_size: int = 100) -> int:
#     """
#     Inserta lecturas horarias de los últimos `days` días para los 25 lotes.
    
#     Usa batches acotados para eficiencia.
#     """
#     collection = connect_astradb("sensor_readings")
#     if collection is None:
#         logger.error("No se pudo conectar a Astra DB. Verificá las variables de entorno.")
#         sys.exit(1)

#     # Limpiamos para no duplicar
#     logger.info("Limpiando sensor_readings…")
#     collection.delete_many({})

#     start_date = datetime.utcnow() - timedelta(days=days)
#     end_date = datetime.utcnow()
#     total = 0

#     logger.info(f"Generando histórico de {days} días para {len(LOTES)} lotes…")

#     for lote in LOTES:
#         docs = []
#         current_time = start_date

#         while current_time < end_date:
#             doc = {
#                 "lote_id": lote,
#                 "timestamp": current_time.replace(microsecond=0).isoformat() + "Z",
#                 "temp": round(random.uniform(15, 35), 2),
#                 "humedad_suelo": round(random.uniform(30, 80), 2),
#                 "precipitacion": round(random.uniform(0, 5) if random.random() > 0.8 else 0.0, 2),
#                 "agua": round(random.uniform(10, 50), 2),
#             }
#             docs.append(doc)
#             total += 1
#             current_time += timedelta(hours=1)

#             # Insert en batches
#             if len(docs) >= batch_size:
#                 try:
#                     collection.insert_many(docs)
#                     docs = []
#                 except Exception as e:
#                     logger.error(f"Error insertando batch para lote {lote}: {e}")
#                     return -1

#         # Insertar docs restantes
#         if docs:
#             try:
#                 collection.insert_many(docs)
#             except Exception as e:
#                 logger.error(f"Error insertando batch final para lote {lote}: {e}")
#                 return -1

#         n_readings = ((end_date - start_date).total_seconds() // 3600)
#         logger.info(f"  lote_id={lote:2d}: insertadas {n_readings:.0f} lecturas")

#     logger.info(f"Listo. {total} documentos insertados en sensor_readings.")
#     return total


# if __name__ == "__main__":
#     generate_iot_data(days=30)
