# AgroPampa S.A. — Datawarehouse AgTech
## UNSAM · Bases de Datos · TP Final 2025

---

## Contexto del proyecto

Pool de siembra en la **Pampa húmeda** (Buenos Aires, Santa Fe, Córdoba).
Cultivos: **soja** (verano) y **trigo** (invierno).
Historial: **3 campañas** — 2022/23, 2023/24 (sequía -18%), 2024/25 (recuperación).
Comercialización: cooperativas locales. Maquinaria: mix propio + tercerizado.

---

## Stack técnico

| Motor | Rol | Acceso |
|-------|-----|--------|
| PostgreSQL via **Supabase** | Datawarehouse (DW) | `SUPABASE_DB_URL` en `.env` |
| **MongoDB Atlas** | Histórico sensores IoT (series temporales) | `MONGODB_URI` en `.env` |
| **Redis Cloud** | Estado tiempo real (última lectura por lote) | `REDIS_URL` en `.env` |
| **Python 3.11+** | ETL: conecta los 3 motores | `etl/pipeline.py` |

**Proyecto Supabase:** `ldfnnrehlehzrdnossre` · región `us-west-2` · estado `ACTIVE_HEALTHY`

---

## Estado actual del TP — qué está hecho y qué falta

### ✅ COMPLETADO

**Ítem 1 — Escenario**
- Empresa, situación y justificación de arquitectura políglota documentadas.

**Ítem 2 — Motores**
- PostgreSQL/Supabase: Open Source, postgresql.org
- MongoDB Atlas: SSPL, mongodb.com/atlas, Free Tier M0
- Redis Cloud: BSD/RSALv2, redis.io/try-free

**Ítem 3 — Diseño del DW**
- Modelo **Copo de Nieve (Snowflake) en 3FN** — 12 tablas, 12 FKs
- DER completo en `sql/schema/schema.dbml` (abrir en dbdiagram.io)
- 11 migraciones aplicadas en Supabase (ver detalle abajo)

**Ítem 4 — Creación e Inserción con ETL**
- DDL creado via migraciones 001-003
- Seeds con datos sintéticos realistas via migraciones 004-011
- 150 filas en `fact_produccion`, 900 en `dim_clima`, 25 lotes, 6 propietarios

---

### ⚠️ PENDIENTE — lo que falta para completar el TP

**Ítem 4 — Operaciones faltantes** (prioridad alta, arrancar por acá)
- [ ] `DELETE` con explicación ETL — baja lógica de un lote inactivo
- [ ] `UPDATE` con explicación ETL — actualización de precio_venta_tn
- [ ] Búsqueda por **1 clave** — `SELECT` por `id` simple
- [ ] Búsqueda por **2 claves** — `SELECT` por `lote_id + campaña`

**Ítem 5 — Minería de datos** (prioridad alta)
- [ ] **Segmentación dinámica**: NTILE + CTE en SQL → clasificar lotes en 3 grupos
  - Variables: `rendimiento_kg_ha`, coeficiente de variación, `tipo_suelo`
  - Grupos: alto rendimiento / medio / bajo riesgo
- [ ] **Predicción dinámica**: regresión lineal OLS en SQL puro
  - Variable independiente: `humedad_promedio` (de `dim_clima`)
  - Variable dependiente: `rendimiento_kg_ha` (de `fact_produccion`)
  - Implementar β₁ = Σ((x-x̄)(y-ȳ)) / Σ((x-x̄)²) y β₀ = ȳ - β₁·x̄ con CTEs

**Ítem 6 — Dashboard BI** (4 elementos mínimos requeridos)
- [ ] Elemento 1: evolución rendimiento por campaña (línea temporal)
- [ ] Elemento 2: producción total por propietario (barras)
- [ ] Elemento 3: mapa de calor de lotes por rendimiento y riesgo
- [ ] Elemento 4: proyección campaña 2025/26

---

### 🔧 CORRECCIÓN PENDIENTE (antes de minería)

**`dim_clima` tiene un problema de diseño:**
- Actualmente usa `lote_id` como FK → genera redundancia con `fact_produccion.lote_id`
- Desde la fact se puede llegar al mismo lote por dos caminos → riesgo de inconsistencia
- **Fix:** reemplazar `lote_id` por `localidad_id` en `dim_clima`
- El clima es un fenómeno geográfico (de zona), no de lote individual
- Migración correctiva pendiente: `012_fix_dim_clima_localidad`

---

## Modelo dimensional — Snowflake en 3FN

### Tabla de hechos
```
fact_produccion
  lote_id FK, cultivo_id FK, tiempo_id FK, maquinaria_id FK, clima_id FK
  rendimiento_kg_ha, superficie_cosechada_ha, costo_total, precio_venta_tn, horas_maquinaria
  granularidad: 1 fila por lote × cultivo × campaña
```

### Jerarquías snowflake (lo que diferencia snowflake de estrella)
```
dim_lote → dim_campo → dim_propietario       (rama propiedad)
                     → dim_localidad → dim_provincia   (rama geográfica)
dim_cultivo    → dim_tipo_cultivo             (rama cultivo)
dim_maquinaria → dim_tipo_maquinaria          (rama maquinaria)
dim_tiempo                                    (sin subdimensiones)
dim_clima      → dim_lote (⚠️ pendiente fix → localidad)
```

### Tablas en producción (Supabase)
| Tabla | Filas | Rol |
|-------|-------|-----|
| `fact_produccion` | 150 | Hechos centrales |
| `dim_lote` | 25 | Subdivisiones del campo |
| `dim_campo` | 9 | Campos 200-600 ha |
| `dim_propietario` | 6 | Dueños |
| `dim_localidad` | 7 | BA / SF / CBA |
| `dim_provincia` | 3 | Pampa húmeda |
| `dim_cultivo` | 6 | Variedades soja/trigo |
| `dim_tipo_cultivo` | 2 | Soja, Trigo |
| `dim_maquinaria` | 9 | Mix propio + tercerizado |
| `dim_tipo_maquinaria` | 5 | Tipos de equipo |
| `dim_tiempo` | 36 | Jul 2022 – Jun 2025 |
| `dim_clima` | 900 | Clima por lote × mes |

---

## Migraciones aplicadas en Supabase

| # | Nombre | Contenido |
|---|--------|-----------|
| 001 | `create_leaf_dimensions` | dim_provincia, dim_tipo_cultivo, dim_tipo_maquinaria, dim_propietario, dim_tiempo |
| 002 | `create_intermediate_dimensions` | dim_localidad, dim_campo, dim_lote, dim_cultivo, dim_maquinaria, dim_clima |
| 003 | `create_fact_produccion` | fact_produccion con 5 FKs e índices |
| 004 | `seed_leaf_dimensions` | 3 provincias, 2 tipos cultivo, 5 tipos maquinaria, 6 propietarios |
| 005 | `seed_geo_dimensions` | 7 localidades (Pergamino, Junín, Venado Tuerto, Rosario, etc.) |
| 006 | `seed_campos` | 9 campos con superficies reales |
| 007 | `seed_lotes` | 25 lotes con tipo de suelo (franco→arenoso) |
| 008 | `seed_cultivos_maquinaria` | 6 variedades + 9 equipos |
| 009 | `seed_dim_tiempo` | 36 meses, campañas 2022/23 a 2024/25 |
| 010 | `seed_dim_clima` | 900 registros con variación por campaña y suelo |
| 011 | `seed_fact_produccion` | 150 hechos con rendimientos N(μ,σ) por tipo de suelo |

---

## Distribuciones usadas en los seeds (para documentar en el TP)

Los rendimientos siguen distribuciones **normales calibradas por tipo de suelo**:

| Tipo suelo | Soja μ (σ) kg/ha | Trigo μ (σ) kg/ha |
|------------|------------------|-------------------|
| Franco | 3.400 (400) | 4.100 (350) |
| Franco-limoso | 3.200 (450) | 3.900 (380) |
| Franco-arcilloso | 3.000 (500) | 3.700 (420) |
| Arcilloso | 2.700 (550) | 3.400 (450) |
| Arenoso | 2.300 (600) | 2.900 (500) |

Factores por campaña: 2022/23 = 1.00 · **2023/24 = 0.82 (sequía)** · 2024/25 = 1.07

Generación aleatoria via **Box-Muller** en SQL puro:
`SQRT(-2·LN(RANDOM())) · COS(2π·RANDOM()) · σ + μ`

---

## Flujo ETL (para documentar en ítem 4)

```
MongoDB (sensor_readings)          Redis (sensor:{id}:*)
        |                                   |
        | pymongo                           | redis-py
        ↓                                   ↓
   extract_sensor_readings()     extract_realtime_state()
        |
        | pandas .groupby() → promedio diario
        ↓
   transform_readings()
        |
        | psycopg2 UPSERT
        ↓
   dim_clima en Supabase
        |
        ↓
   fact_produccion (queries de BI y minería)
```

El ETL corre en `etl/pipeline.py`. Cada función tiene rol separado:
- `etl/extractors/` → lectura cruda desde NoSQL
- `etl/transformers/` → agregación, limpieza, outliers
- `etl/loaders/` → UPSERT idempotente en Supabase

---

## Comandos slash disponibles en Claude Code

Están en `.claude/commands/`. Usarlos con `/nombre` en Claude Code:

| Comando | Qué hace |
|---------|----------|
| `/schema` | Regenera el DDL completo de todas las tablas |
| `/seeds` | Genera datos sintéticos realistas para todas las tablas |
| `/etl` | Construye el pipeline ETL completo (extract→transform→load) |
| `/mining` | Genera las queries de segmentación y predicción |

---

## Variables de entorno necesarias

Ver `.env.example`. Crear `.env` local con:
```
SUPABASE_DB_URL=postgresql://postgres:...@db.ldfnnrehlehzrdnossre.supabase.co:5432/postgres
SUPABASE_URL=https://ldfnnrehlehzrdnossre.supabase.co
SUPABASE_KEY=eyJ...
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/agtech_sensors
REDIS_URL=redis://default:pass@host:port
```

---

## Convenciones de código

- SQL: `snake_case`, PKs `SERIAL PRIMARY KEY`, FKs nombradas `fk_{tabla}_{columna}`
- Migraciones: numeradas `NNN_nombre_en_snake_case.sql`, siempre idempotentes (`IF NOT EXISTS`)
- Python: una función por paso ETL, logging estándar, nunca hardcodear credenciales
- Cada función ETL: docstring con qué hace, parámetros y qué retorna

---

## Próximo paso sugerido

```
1. Corregir dim_clima: migración 012_fix_dim_clima_localidad
2. Queries operaciones faltantes: DELETE, UPDATE, búsquedas 1 y 2 claves
3. Minería: /mining → segmentación NTILE + predicción OLS
4. Dashboard BI: 4 elementos en React/HTML conectados a Supabase
```