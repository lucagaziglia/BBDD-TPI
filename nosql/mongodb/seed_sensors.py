"""
Genera 18,000 registros aproximadamente (25 lotes × 30 días × 24 lecturas por día).

Simula:

Periodicidad: Una lectura cada 1 hora de forma ininterrumpida.

Cobertura: 25 lotes diferentes (identificados del 1 al 25).

Variables Climáticas y de Suelo:

temp: Calor ambiente (entre 15°C y 35°C).

humedad_suelo: Qué tan regada está la tierra (30% a 80%).

precipitacion: Lluvia. Tiene una lógica de probabilidad: el 80% de las veces marca 0 (no llueve), y el 20% restante genera entre 0 y 5mm.

agua: Consumo de riego (10 a 50 unidades).

3. Qué se "Extrae" de los Sensores (El esquema)
Cada lectura es un documento JSON que contiene:

lote_id: A qué lote pertenece la medición.

timestamp: Fecha y hora exacta del reporte.

temp, humedad_suelo, precipitacion, agua: Los valores crudos medidos.

"""

import os
import random
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# Configuración
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "agropampa_nosql"
COLLECTION = "sensor_readings"

def generate_iot_data(days=30):
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    col = db[COLLECTION]
    
    # Limpiamos para no duplicar en el test
    col.delete_many({}) 
    
    lotes = range(1, 26) # Tus 25 lotes
    start_date = datetime.now() - timedelta(days=days)
    
    records = []
    print(f"--- Generando datos para {days} días ---")

    for lote in lotes:
        current_time = start_date
        while current_time < datetime.now():
            # Simulamos una lectura cada 1 hora
            # Usamos los nombres exactos que tu transformer ya sabe mapear
            reading = {
                "lote_id": lote,
                "timestamp": current_time,
                "temp": round(random.uniform(15, 35), 2),
                "humedad_suelo": round(random.uniform(30, 80), 2),
                "precipitacion": round(random.uniform(0, 5) if random.random() > 0.8 else 0, 2),
                "agua": round(random.uniform(10, 50), 2)
            }
            records.append(reading)
            current_time += timedelta(hours=1)
            
            # Insertamos en batches para no saturar la memoria
            if len(records) >= 1000:
                col.insert_many(records)
                records = []
                
    if records:
        col.insert_many(records)
        
    print(f"Finalizado: {col.count_documents({})} registros insertados en MongoDB.")

if __name__ == "__main__":
    generate_iot_data(30)