# AgTech Datawarehouse - TP Final BBDD

Bienvenido al repositorio del Trabajo Práctico Final de la materia Bases de Datos (UNSAM).

## Setup e Instrucciones

1. **Clonar repositorio e instalar dependencias:**
   ```bash
   git clone <repo_url>
   cd BBDD-TPI
   pip install -r requirements.txt
   ```

2. **Configuración de Variables de Entorno:**
   Copia el archivo `.env.example` a `.env` y completa con las credenciales de los diferentes motores:
   - Supabase (PostgreSQL)
   - MongoDB Atlas
   - Redis Cloud
   ```bash
   cp .env.example .env
   ```

3. **Ejecutar el Pipeline:**
   Puedes utilizar Claude Code con los comandos definidos en `.claude/commands/` o ejecutar directamente Python:
   ```bash
   python etl/pipeline.py
   ```

Para más contexto y convenciones, lee el archivo `CLAUDE.md`.

## SQL — Orden de ejecución

La carpeta `sql/` contiene el modelo dimensional completo. Ejecutar en este orden:

```
# 1. Schema (DDL) — crear tablas vacías
sql/schema/01_dimensions_leaf.sql        # dim_provincia, dim_tipo_cultivo, dim_propietario, dim_tiempo
sql/schema/02_dimensions_intermediate.sql # dim_localidad, dim_campo, dim_cultivo, dim_maquinaria
sql/schema/03_dimensions_main.sql        # dim_lote, dim_clima
sql/schema/04_fact.sql                   # fact_produccion

# 2. Seeds — poblar con datos sintéticos
sql/seeds/01_seed_provincias.sql
sql/seeds/02_seed_tipos.sql
sql/seeds/03_seed_propietarios.sql
sql/seeds/04_seed_localidades.sql
sql/seeds/05_seed_campos.sql
sql/seeds/06_seed_lotes.sql
sql/seeds/07_seed_cultivos_maquinaria.sql
sql/seeds/08_seed_tiempo.sql
sql/seeds/09_seed_fact.sql

# 3. Operaciones DML (consigna ítems 4.x)
sql/operations/delete_ejemplo.sql
sql/operations/update_ejemplo.sql
sql/operations/busqueda_1_clave.sql
sql/operations/busqueda_2_claves.sql

# 4. Queries analíticas
sql/queries/bi/rendimiento_por_campania.sql
sql/queries/bi/produccion_por_propietario.sql
sql/queries/mining/segmentacion_lotes.sql
sql/queries/mining/prediccion_rendimiento.sql
```
