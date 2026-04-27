/**
 * Schema Validation de MongoDB para la colección sensor_readings
 * Colección: histórico crudo de sensores IoT
 * Motor: MongoDB Atlas
 */

db.createCollection("sensor_readings", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: [ "sensor_id", "lote_id", "timestamp", "tipo_lectura", "valor" ],
         properties: {
            sensor_id: {
               bsonType: "string",
               description: "ID único del sensor IoT"
            },
            lote_id: {
               bsonType: "int",
               description: "FK: ID del lote (conecta con Supabase)"
            },
            timestamp: {
               bsonType: "date",
               description: "Momento exacto de la medición"
            },
            tipo_lectura: {
               enum: [ "HUMEDAD_SUELO", "TEMPERATURA", "PRECIPITACION", "RADIACION" ],
               description: "Tipo de métrica registrada"
            },
            valor: {
               bsonType: "double",
               description: "Valor numérico de la lectura"
            }
         }
      }
   }
});

// Índice compuesto para acelerar las extracciones del ETL (por fecha y lote)
db.sensor_readings.createIndex({ timestamp: 1, lote_id: 1 });
