# AgTech Datawarehouse — UNSAM Bases de Datos TP Final

## Contexto del Proyecto

Sistema de inteligencia de negocios para una empresa AgTech que gestiona campos,
cultivos, maquinaria y sensores IoT. Arquitectura políglota con tres motores:

| Motor        | Rol                              | Acceso                  |
|--------------|----------------------------------|-------------------------|
| Supabase     | Datawarehouse (PostgreSQL)       | `SUPABASE_URL` + `SUPABASE_KEY` |
| MongoDB Atlas| Histórico de sensores (documentos)| `MONGODB_URI`           |
| Redis Cloud  | Estado en tiempo real (key-value)| `REDIS_URL`             |

## Estructura del Repositorio

```
agtech-dw/
├── CLAUDE.md                  # Este archivo
├── .claude/
│   ├── settings.json          # Permisos de Claude Code
│   └── commands/              # Comandos slash personalizados
├── docs/                      # Documentación del TP
├── infra/                     # docker-compose de desarrollo local (opcional)
├── etl/
│   ├── extractors/            # Lectura desde MongoDB y Redis
│   ├── transformers/          # Limpieza y transformación
│   └── loaders/               # Carga hacia Supabase/PostgreSQL
├── sql/
│   ├── schema/                # DDL: tablas de hechos y dimensiones
│   ├── migrations/            # Migraciones numeradas (001_, 002_, ...)
│   ├── seeds/                 # Datos sintéticos para poblar el DW
│   └── queries/
│       ├── mining/            # Consultas de minería de datos
│       └── bi/                # Consultas para el dashboard
├── nosql/
│   ├── mongodb/               # Schemas de colecciones y scripts
│   └── redis/                 # Estructura de keys y scripts
├── dashboard/                 # Visualizaciones BI
└── tests/                     # Tests de cada capa ETL
```

## Modelo Dimensional (Estrella)

### Tabla de Hechos Principal
`fact_produccion` — granularidad: una fila por lote × campaña × período

### Dimensiones
- `dim_campo` — campos y dueños
- `dim_lote` — subdivisiones del campo
- `dim_cultivo` — tipo de cultivo (soja, trigo, maíz)
- `dim_tiempo` — jerarquía temporal (día → mes → trimestre → campaña)
- `dim_maquinaria` — equipos y estado
- `dim_clima` — condiciones meteorológicas agregadas

### Colecciones MongoDB
- `sensor_readings` — lecturas crudas de sensores (humedad, temperatura)
- `riego_events` — eventos de activación/desactivación del riego

### Keys Redis
- `sensor:{lote_id}:humedad` — último valor de humedad (string, float)
- `sensor:{lote_id}:temperatura` — último valor de temperatura
- `riego:{lote_id}:estado` — ON/OFF del sistema de riego

## Stack Técnico

- **Python 3.11+** para todo el ETL y scripts
- **psycopg2** o **supabase-py** para conectar con Supabase
- **pymongo** para MongoDB Atlas
- **redis-py** para Redis Cloud
- **pandas** para transformaciones en el ETL
- **faker** + datos sintéticos reales de MAGYP para seeds

## Convenciones de Código

### SQL
- Tablas en `snake_case`
- PKs siempre `id SERIAL PRIMARY KEY` o `UUID`
- FKs explícitas con nombre: `fk_{tabla}_{columna}`
- Migraciones numeradas: `001_create_dimensions.sql`, `002_create_facts.sql`
- Todo DDL debe ser idempotente (`CREATE TABLE IF NOT EXISTS`)

### Python
- Una función por operación ETL (extract / transform / load separados)
- Logging explícito en cada paso del pipeline
- Variables de entorno para credenciales — NUNCA hardcodear
- Cada script ETL debe poder correrse de forma independiente

### Estructura de un script ETL tipo
```python
# etl/extractors/mongodb_sensor_extractor.py
def extract_sensor_readings(desde: datetime, hasta: datetime) -> list[dict]:
    """
    Extrae lecturas de sensores de MongoDB Atlas.
    Retorna lista de documentos crudos sin transformar.
    """
    ...

def transform_readings(raw: list[dict]) -> pd.DataFrame:
    """
    Limpia y estandariza lecturas. Maneja nulls y outliers.
    Retorna DataFrame listo para cargar.
    """
    ...

def load_to_staging(df: pd.DataFrame, conn) -> int:
    """
    Carga al staging de Supabase. Retorna cantidad de filas insertadas.
    """
    ...
```

## Variables de Entorno

Siempre leer de `.env` (nunca hardcodear). Archivo `.env.example` como referencia:

```
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/agtech
REDIS_URL=redis://default:pass@redis-cloud-host:port
```

## Qué hacer al empezar una tarea

1. Revisar `sql/schema/` para entender el modelo dimensional vigente
2. Revisar `etl/` para no duplicar lógica existente
3. Para cualquier script nuevo, crear primero la función de extracción, luego transformación, luego carga
4. Testear con `seeds/` antes de correr sobre datos reales

## Contexto Académico

- **Materia:** Bases de Datos — UNSAM
- **Trabajo:** TP Final — Datawarehouse AgTech
- **Entregables requeridos:** Schema DW, ETL documentado, Minería de datos (segmentación + predicción), Dashboard BI con ≥4 elementos
- **Motores:** PostgreSQL (Supabase) + MongoDB Atlas + Redis Cloud

## Notas Importantes

- El TP exige explicar cada operación ETL: cada script debe tener docstrings claros
- Las consultas de minería deben incluir comentarios explicando la lógica
- El modelo estrella es preferible al copo de nieve para este escenario (menor complejidad de JOINs para el dashboard)
