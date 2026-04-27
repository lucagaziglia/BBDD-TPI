# Redis Cloud - Estructura de Keys (Tiempo Real)

Redis se utiliza como una capa de estado rápido (key-value store). Su propósito en este Datawarehouse es almacenar la "última foto" del campo para que la app de los agrónomos la lea sin pegarle a MongoDB.

## Patrones de Keys utilizados

| Key Pattern | Data Type | Ejemplo de Valor | Descripción |
|---|---|---|---|
| `sensor:{lote_id}:{tipo}` | `String` | `"24.5"` | Último valor registrado de humedad o temp. |
| `sensor:{lote_id}:ts` | `String` | `"2025-01-20T14:30:00Z"` | Timestamp de la última lectura. |
| `alerta:{lote_id}` | `String` (con TTL) | `"HUMEDAD_BAJA"` | Alertas efímeras (ej. expiran en 2 horas). |
| `maq:{equipo_id}` | `Hash` | `{"lat": "-34.5", "status": "ON"}` | Posición GPS y estado del tractor/cosechadora. |

## Ejemplos de Comandos CLI

```bash
# Insertar lectura de sensor
SET sensor:12:HUMEDAD_SUELO "18.5"
SET sensor:12:ts "2025-02-10T10:00:00Z"

# Generar alerta que se borra sola en 1 hora (3600 seg)
SETEX alerta:12 3600 "REVISAR_RIEGO"

# Actualizar telemetría de cosechadora
HSET maq:5 lat "-34.882" lon "-60.213" status "COSECHANDO"
```
